import csv
import sys
import os
import time

# 导入本项目核心清洗与双引擎模块
from eval_pipeline import dual_engine_audit

# Windows 终端 UTF-8 兼容
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

SAMPLE_INPUT_PATH = os.path.join(os.path.dirname(__file__), "sample_campaign_input.csv")
SAMPLE_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "audited_campaign_output.csv")

def create_sample_input_csv():
    """生成运营常见的营销文案待审表格样例"""
    sample_data = [
        ["ID", "商品名称", "推广渠道", "待审推广文案"],
        ["SKU001", "玻尿酸保湿面霜", "小红书", "换季温和补水，质地轻盈柔润，干皮日常保湿锁水首选。"],
        ["SKU002", "紧致抗皱精华", "抖音直播", "全网第①抗老精华！顶_级修护成分，3天彻底根除细纹法令纹！"],
        ["SKU003", "高山有机红富士", "天猫淘宝", "新鲜采摘直发，脆甜多汁无农残，全家老少健康水果日常。"],
        ["SKU004", "清肺草本养生茶", "微信私域", "纯天然药效持久，加vx领券，彻底根治支气管炎哮喘降三高！"],
        ["SKU005", "降噪头戴式耳机", "天猫淘宝", "军工_品质航天芯片，原价999今晚跳楼_价99元，全网最_低！"],
        ["SKU006", "洋甘菊舒缓喷雾", "小红书", "换季脸颊干燥紧绷时喷一喷，水雾细腻，为肌肤补充日常水分。"],
        ["SKU007", "美白淡斑小奶瓶", "抖音直播", "全网die一美白神器，一夜换*皮，100%消灭所有色斑暗沉！"],
        ["SKU008", "加厚白鹅绒服", "天猫淘宝", "90%高蓬松白鹅绒，防风锁温，通过国家纺织品质检标准。"],
        ["SKU009", "微整涂抹水光针", "微信私域", "院线级消_炎断根原液，医美平替，一次见效永不复发！"],
        ["SKU010", "免洗速干洗手液", "天猫淘宝", "温和抑菌洁净双手，含芦荟保湿精华，清新不伤手。"]
    ]
    with open(SAMPLE_INPUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(sample_data)
    print(f"📄 待审文案样本已生成: {SAMPLE_INPUT_PATH}")

def generate_mock_rewrites(raw_text: str, matched_words: list) -> dict:
    """针对违规文案，生成3种合规商业转化方案"""
    return {
        "geek": "采用规范化生产工艺，具体成分与功效以产品备案为准。适合日常干燥紧绷时使用，提供温和保湿护理，水润感因人而异。",
        "scene": "掌心温度乳化后轻按上脸，肤感柔嫩润滑，不承诺即时改变，只把日常保湿滋润做好，后续上妆体验因人而异。",
        "empathy": "换季干燥、状态不稳？别急着叠加太多猛药，把基础保湿做扎实，为肌肤提供日常滋润护理，效果因人而异。"
    }

def batch_audit_file(input_file: str, output_file: str):
    """
    批量执行风控审查，并导出带审计状态、罚金估算和3种改写方案的 Excel/CSV
    """
    if not os.path.exists(input_file):
        print(f"❌ 找不到输入文件: {input_file}，正在自动生成样例...")
        create_sample_input_csv()

    print(f"\n================================================================")
    print(f"📊 正在批量审查运营推广文案: {input_file}")
    print(f"================================================================")

    results = []
    with open(input_file, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)

    out_headers = headers + ["风控判定", "风险等级", "命中违禁词", "预估罚金区间", "改写方案A(成分极客)", "改写方案B(场景种草)", "改写方案C(痛点共鸣)"]

    total = len(rows)
    violation_count = 0

    for idx, row in enumerate(rows, 1):
        raw_text = row.get("待审推广文案", "")
        audit_res = dual_engine_audit(raw_text)
        has_v = audit_res["has_violation"]
        words = audit_res["matched_words"]

        if has_v:
            violation_count += 1
            risk_level = "极高风险（触发顶格硬拦截）" if len(words) >= 2 else "中高风险"
            est_fine = "20 万元 ~ 100 万元" if len(words) >= 2 else "10 万元 ~ 50 万元"
            decision = "❌ 强制驳回"
            rewrites = generate_mock_rewrites(raw_text, words)
            print(f"[{idx:02d}/{total:02d}] ❌ {row.get('商品名称'):<10} | 命中违禁词: {words} -> 拦截")
        else:
            risk_level = "合规/低风险"
            est_fine = "0 元"
            decision = "✅ 准予放行"
            rewrites = {"geek": "-", "scene": "-", "empathy": "-"}
            print(f"[{idx:02d}/{total:02d}] ✅ {row.get('商品名称'):<10} | 无违规用语 -> 准予放行")

        row_out = dict(row)
        row_out["风控判定"] = decision
        row_out["风险等级"] = risk_level
        row_out["命中违禁词"] = "、".join(words) if words else "无"
        row_out["预估罚金区间"] = est_fine
        row_out["改写方案A(成分极客)"] = rewrites["geek"]
        row_out["改写方案B(场景种草)"] = rewrites["scene"]
        row_out["改写方案C(痛点共鸣)"] = rewrites["empathy"]
        results.append(row_out)

    # 导出 utf-8-sig 编码文件，保证在 WPS / Excel 打开绝无乱码
    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_headers)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n================================================================")
    print(f"🎉 批量风控审计完成！")
    print(f"📈 总处理样本: {total} 条 | 违规拦截: {violation_count} 条 | 合规放行: {total - violation_count} 条")
    print(f"💾 审查结果与改写方案已保存至: {output_file}")
    print(f"================================================================")

if __name__ == "__main__":
    if not os.path.exists(SAMPLE_INPUT_PATH):
        create_sample_input_csv()
    batch_audit_file(SAMPLE_INPUT_PATH, SAMPLE_OUTPUT_PATH)
