"""
核心编排层（LangGraph）

将原来分散在 workflows/ 下的三个独立小图，重构为一张带两次人工中断
（human_select / human_review）的统一图文生成工作流：

    START
      -> plan_topics                # AI 生成 3-5 个选题
      -> human_select   [interrupt] # 暂停：等待人工选择 selected_topic
      -> generate_draft             # 撰写长文（驳回时带 human_feedback 重写）
      -> human_review   [interrupt] # 暂停：等待人工通过 / 驳回
      -> 条件路由
           approve -> extract_visual_points  # 提炼 3-5 个视觉知识点
                    -> generate_images       # 并行绘图
                    -> END
           reject  -> generate_draft         # 回环重写
"""
