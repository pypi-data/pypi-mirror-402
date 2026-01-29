#!/bin/bash

# Meta Prompt Wrapper
# Takes a refined prompt and wraps it with recursive meta-cognition instructions
# for AI code generators (Claude Code, Copilot, Cursor, etc.)

# Spinner animation frames
SPINNER_FRAMES=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
BRAIN_FRAMES=("🧠" "💭" "✨" "💡")

show_spinner() {
    local pid=$1
    local start_time=$(date +%s)
    local frame_idx=0
    local brain_idx=0

    if [[ -t 2 ]]; then
        printf '\033[?25l' >&2
    fi

    while kill -0 "$pid" 2>/dev/null; do
        local elapsed=$(($(date +%s) - start_time))
        local spinner="${SPINNER_FRAMES[$frame_idx]}"
        local brain="${BRAIN_FRAMES[$brain_idx]}"

        printf "\r  %s %s Wrapping prompt... [%02d:%02d] " "$brain" "$spinner" $((elapsed/60)) $((elapsed%60)) >&2

        frame_idx=$(( (frame_idx + 1) % ${#SPINNER_FRAMES[@]} ))
        if (( frame_idx == 0 )); then
            brain_idx=$(( (brain_idx + 1) % ${#BRAIN_FRAMES[@]} ))
        fi

        sleep 0.1
    done

    printf "\r%-50s\r" "" >&2
    if [[ -t 2 ]]; then
        printf '\033[?25h' >&2
    fi
}

call_llm() {
    local prompt="$1"
    local api_key="sk-6f86f804bba64048b1ab34dc36ed9a0c"
    local api_url="https://api.deepseek.com/chat/completions"

    local messages_json
    if command -v jq &> /dev/null; then
        messages_json=$(jq -n --arg p "$prompt" '[{"role": "user", "content": $p}]')
    else
        messages_json=$(printf '[{"role": "user", "content": "%s"}]' "$(echo "$prompt" | sed 's/"/\\"/g')")
    fi

    local tokens="${MAX_TOKENS:-1000}"
    local json_payload
    json_payload=$(printf '{
        "model": "deepseek-chat",
        "messages": %s,
        "max_tokens": %s,
        "temperature": 0.7
    }' "$messages_json" "$tokens")

    local tmp_file=$(mktemp)

    curl -s --max-time 60 -X POST "$api_url" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $api_key" \
        -d "$json_payload" \
        -w "\nHTTP_CODE:%{http_code}" > "$tmp_file" 2>&1 &

    local curl_pid=$!
    show_spinner "$curl_pid"
    wait "$curl_pid"

    local response
    response=$(cat "$tmp_file")
    rm -f "$tmp_file"

    local http_code
    http_code=$(echo "$response" | tail -1 | sed 's/HTTP_CODE://')
    response=$(echo "$response" | sed '$d')

    if [[ "$http_code" != "200" ]]; then
        echo "[ERROR] API returned HTTP $http_code" >&2
    fi

    local content
    if command -v jq &> /dev/null; then
        content=$(echo "$response" | jq -r '.choices[0].message.content')
    else
        content=$(echo "$response" | grep -o '"content":"[^"]*' | sed 's/"content":"//' | head -n 1)
    fi

    echo "$content"
}

# --- Main script ---

layers=3
max_tokens=1000

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -p|--prompt) refined_prompt="$2"; shift ;;
        -l|--layers) layers="$2"; shift ;;
        -t|--max-tokens) max_tokens="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$refined_prompt" ]; then
    echo "Error: --prompt is required."
    echo "Usage: $0 --prompt \"Your refined prompt\" [--layers N] [--max-tokens N]"
    exit 1
fi

export MAX_TOKENS="$max_tokens"

echo "" >&2
echo "╔════════════════════════════════════════╗" >&2
echo "║  🔄 Generating Meta-Cognition Wrapper  ║" >&2
echo "╚════════════════════════════════════════╝" >&2

wrapper_instruction="You are creating a meta-prompt for AI code assistants (Claude Code, Cursor, Copilot).

The user has this refined technical prompt:
\"\"\"
$refined_prompt
\"\"\"

Your task: Wrap this prompt with recursive meta-cognition instructions that tell the code assistant to:

1. **Layer-based implementation**: Break the task into $layers distinct layers/phases
2. **Self-reflection after each layer**: After completing each layer, pause and evaluate:
   - What was implemented correctly?
   - What edge cases might be missing?
   - What could be improved before proceeding?
3. **Iterative refinement**: Apply improvements before moving to the next layer
4. **Final review**: After all layers, do a comprehensive self-review

Structure the output as a complete prompt that:
- Starts with clear instructions about the recursive meta-cognition approach
- Includes the original technical requirements
- Specifies the layer breakdown
- Defines what self-reflection questions to ask at each layer
- Ends with final validation criteria

Output ONLY the wrapped meta-prompt. No explanations outside the prompt itself. The output should be ready to paste directly into a code assistant."

response=$(call_llm "$wrapper_instruction")

echo "" >&2
echo "  ✓ Complete" >&2
echo "" >&2
echo "╔════════════════════════════════════════╗" >&2
echo "║  ✅ Meta-Cognition Wrapped Prompt      ║" >&2
echo "╚════════════════════════════════════════╝" >&2
echo ""
echo "$response"
