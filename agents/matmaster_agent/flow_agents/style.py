def plan_ask_confirm_card():
    return """
<div style="
  background-color: #e7f3ff;
  border: 1px solid #b3d9ff;
  border-left: 4px solid #0066cc;
  border-radius: 4px;
  padding: 12px 16px;
  margin: 12px 0;
  font-family: sans-serif;
  color: #004085;
  line-height: 1.4;
">
  <strong>请确认是否执行上述计划？</strong>
</div>
"""


def parameters_ask_confirm_card():
    return """
<div style="
  background-color: #fff3cd;
  border: 1px solid #ffc107;
  border-left: 4px solid #ff9800;
  border-radius: 4px;
  padding: 12px 16px;
  margin: 12px 0;
  font-family: sans-serif;
  color: #856404;
  line-height: 1.4;
">
  <strong>请确认上述参数是否正确？确认后将生成参数 JSON 文件。</strong>
</div>
"""
