import json
import sys
import os
import urllib.request

# Windows 终端 UTF-8 兼容
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

def build_feishu_card_payload(raw_text: str, risk_level: str, est_fine: str, matched_words: list, rewrites: dict) -> dict:
    """
    构造符合飞书官方规范的交互式富文本报警卡片 JSON
    """
    matched_words_str = "、".join([f"**「{w}」**" for w in matched_words])
    
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "red",
                "title": {
                    "tag": "plain_text",
                    "content": "🚨 【法务红线】电商广告法违规拦截与重构通知"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**⚠️ 拦截状态**：<font color='red'>{risk_level}</font>\n"
                                   f"**💰 预估行政罚款**：**{est_fine}**\n"
                                   f"**🔍 命中高危违禁词**：{matched_words_str}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**📝 原始提审文案**：\n> {raw_text}"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**💡 双智能体 (Actor-Critic) 靶向改写方案 (可直接使用)**：\n"
                                   f"• **[成分极客风]**：{rewrites.get('geek', '围绕基础保湿设计，产品按化妆品相关标准生产...')}\n\n"
                                   f"• **[场景种草风]**：{rewrites.get('scene', '晚上洗完脸，掌心温度乳化，润而不黏，上妆体验因人而异...')}\n\n"
                                   f"• **[痛点共鸣风]**：{rewrites.get('empathy', '换季干燥空调房紧绷？把基础保湿做扎实，日常滋润更安心...')}"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "📋 复制推荐改写文案"
                            },
                            "type": "primary",
                            "value": {
                                "action": "copy_compliant_text"
                            }
                        },
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "⚖️ 查看法务质检批注"
                            },
                            "type": "default",
                            "value": {
                                "action": "view_critic_notes"
                            }
                        }
                    ]
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": "🤖 由 Dual-Engine E-Commerce Compliance Agent 自动生成并推送到风控审核群"
                        }
                    ]
                }
            ]
        }
    }
    return card

def send_alert_to_feishu(webhook_url: str, card_payload: dict) -> bool:
    """
    向飞书机器人 Webhook 推送告警卡片
    """
    try:
        data = json.dumps(card_payload).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            if res_json.get("StatusCode") == 0 or res_json.get("code") == 0:
                print("✅ 飞书卡片推送成功！")
                return True
            else:
                print(f"❌ 飞书接口返回错误: {res_body}")
                return False
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False

def simulate_card_preview():
    # 模拟一条典型对抗高危用例
    sample_raw = "全网第①面霜！顶_级修护成分，彻底根除泛红敏感，换季烂脸三天换皮！"
    sample_risk = "极高风险（触发顶格硬拦截）"
    sample_fine = "20 万元 ~ 100 万元（触发广告法第57条）"
    sample_matched = ["全网第1", "顶级", "根除", "换皮"]
    sample_rewrites = {
        "geek": "换季面霜走日常保湿护理思路：采用规范生产工艺，质地柔润，为肌肤提供日常保湿护理，具体以产品标签为准。",
        "scene": "换季那几天两颊干紧？绵柔乳霜触肤即化，不承诺即时改变肤感，只做好日常温润保湿，后续上妆体验因人而异。",
        "empathy": "换季干燥、上妆卡粉？别急着叠猛药，把日常保湿做扎实，为干燥紧绷肌肤提供日常滋润护理，效果因人而异。"
    }

    card = build_feishu_card_payload(sample_raw, sample_risk, sample_fine, sample_matched, sample_rewrites)
    
    print("=" * 64)
    print("📱 飞书 / 钉钉交互式告警卡片 JSON Schema 预览")
    print("=" * 64)
    print(json.dumps(card, ensure_ascii=False, indent=2))
    print("=" * 64)
    print("💡 如何在 Dify 工作流中直接使用：")
    print("1. 在 Dify 画布的【Refiner】节点后添加一个【HTTP 请求】节点；")
    print("2. 请求方法选 POST，URL 填你的飞书自定义机器人 Webhook 地址；")
    print("3. Body 类型选 JSON，直接引用上述 Card Schema 变量；")
    print("4. 一旦风控判定为高危，飞书群里即可秒级收到带颜色的交互卡片！")
    print("=" * 64)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        webhook = sys.argv[1]
        print(f"🚀 正在向真实 Webhook 推送告警: {webhook}")
        # 演示调用
        card = build_feishu_card_payload(
            raw_text="全网第①面霜！顶_级修护成分，彻底根除泛红敏感，换季烂脸三天换皮！",
            risk_level="极高风险（触发顶格硬拦截）",
            est_fine="20 万元 ~ 100 万元",
            matched_words=["全网第1", "顶级", "根除", "换皮"],
            rewrites={}
        )
        send_alert_to_feishu(webhook, card)
    else:
        simulate_card_preview()
