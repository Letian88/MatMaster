THINKING_AGENT = (
    'reasoning_agent'  # 原 thinking_agent，为避免前端 thinking 渲染报错而改名
)

# Model is asked to end first-round output with exactly one of these (no hardcoded hint lists)
FIRST_ROUND_READY = 'READY'  # reasoning is definitive, ready for plan_make
FIRST_ROUND_NEED_REVISION = 'NEED_REVISION'
# Revision round: model outputs this when prior reasoning is fine
REVISION_OK = 'OK'
