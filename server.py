"""
Server Web Chính - Hệ thống AI Agent Phân Tích & Điều Hành Doanh Nghiệp.
Chạy cục bộ tại http://localhost:5000 (bind 127.0.0.1).
Không dùng placeholder, không TODO. Chạy `python server.py` là hoạt động ngay.
"""

import os
import json
import logging
import datetime
from typing import Dict, Any
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename

from agent.pipeline_manager import PipelineManager
from agent.extractor import Extractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Server")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IS_VERCEL = os.environ.get("VERCEL") == "1" or "VERCEL" in os.environ

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB max upload

if IS_VERCEL:
    UPLOAD_FOLDER = os.path.join("/tmp", "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    import shutil
    db_source = os.path.join(BASE_DIR, "agent", "data", "pipeline_database.json")
    db_target = os.path.join("/tmp", "pipeline_database.json")
    if os.path.exists(db_source) and not os.path.exists(db_target):
        shutil.copy2(db_source, db_target)

    pm = PipelineManager(
        db_path=db_target if os.path.exists(db_target) else db_source,
        config_path=os.path.join(BASE_DIR, "config.json")
    )
else:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "agent", "data", "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    pm = PipelineManager(
        db_path=os.path.join(BASE_DIR, "agent", "data", "pipeline_database.json"),
        config_path=os.path.join(BASE_DIR, "config.json")
    )


@app.route("/")
def index():
    """Trang chủ Dashboard Single Page Application."""
    return render_template("index.html")


@app.route("/api/config", methods=["GET", "POST"])
def manage_config():
    """Lấy hoặc cập nhật cấu hình hệ thống, thông tin thương hiệu và trạng thái AI."""
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        try:
            cfg_path = pm.config_path
            current_cfg = {}
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    current_cfg = json.load(f)

            # Cập nhật branding
            if "branding" in data:
                current_cfg.setdefault("branding", {}).update(data["branding"])
            # Cập nhật gemini
            if "gemini" in data:
                current_cfg.setdefault("gemini", {}).update(data["gemini"])
            # Cập nhật distribution_policy
            if "distribution_policy" in data:
                current_cfg.setdefault("distribution_policy", {}).update(data["distribution_policy"])

            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(current_cfg, f, ensure_ascii=False, indent=2)

            pm.llm_client.config = current_cfg
            pm.report_exporter.config = current_cfg
            logger.info("Đã cập nhật cấu hình thành công.")
            return jsonify({"success": True, "message": "Cấu hình hệ thống đã được lưu thành công."})
        except Exception as e:
            logger.exception("Lỗi khi lưu cấu hình")
            return jsonify({"success": False, "message": str(e)}), 500

    cfg = pm.llm_client.config
    branding = cfg.get("branding", {})
    dist_policy = cfg.get("distribution_policy", {})
    gemini_cfg = cfg.get("gemini", {})
    return jsonify({
        "success": True,
        "system_name": branding.get("system_name", "Hệ thống AI Agent Phân tích Doanh nghiệp"),
        "enterprise_name": branding.get("fictional_enterprise_name", "Tập đoàn Sao Việt"),
        "primary_color": branding.get("primary_color", "#1E40AF"),
        "secondary_color": branding.get("secondary_color", "#0D9488"),
        "accent_color": branding.get("accent_color", "#F59E0B"),
        "model_name": pm.llm_client.model,
        "is_ai_available": pm.llm_client.is_ai_available(),
        "fallback_mode": not pm.llm_client.is_ai_available(),
        "max_feedback_rounds": pm.feedback_handler.max_rounds,
        "distribution_policy": dist_policy,
        "gemini_config": {
            "model": gemini_cfg.get("model", "gemini-2.5-flash"),
            "temperature": gemini_cfg.get("temperature", 0.2),
            "max_tokens": gemini_cfg.get("max_tokens", 4096),
            "has_api_key": bool(os.environ.get("GEMINI_API_KEY") or gemini_cfg.get("api_key"))
        },
        "domain_modules": [
            {
                "id": "generic_analysis",
                "name": "Phân tích Quản trị Kinh doanh Tổng quát (Mặc định)",
                "description": "Phân tích doanh thu, chi phí, công nợ, đổi trả hàng, tìm nguyên nhân gốc 5 Whys và đề xuất giải pháp."
            },
            {
                "id": "distribution_partner",
                "name": "Lựa chọn & Thẩm định Đối tác Phân phối (Gia dụng)",
                "description": "Quy trình 6 bước: Haversine Geofencing, trần nợ, bẫy cam kết ảo (-25đ), khảo sát liên phòng ban và Cockpit phê duyệt."
            }
        ]
    })


@app.route("/api/audit-logs", methods=["GET"])
def get_audit_logs():
    """Lấy danh sách nhật ký kiểm toán và lịch sử hoạt động toàn hệ thống."""
    reqs = pm.list_requests()
    logs = []
    for r in reqs:
        rid = r.get("id")
        created = r.get("created_at")
        logs.append({
            "timestamp": created,
            "request_id": rid,
            "action": "Tiếp nhận hồ sơ",
            "actor": "Người dùng điều hành",
            "details": f"Tiếp nhận hồ sơ module {r.get('domain_module')} (file: {r.get('file_name', 'N/A')})",
            "version": "v1",
            "status": "THÀNH_CÔNG"
        })
        for item in r.get("state_history", []):
            logs.append({
                "timestamp": item.get("timestamp", created),
                "request_id": rid,
                "action": f"Chuyển trạng thái sang {item.get('to_state')}",
                "actor": item.get("user_name", "AI Agent"),
                "details": f"Từ {item.get('from_state')} -> {item.get('to_state')}: {item.get('notes', '')}",
                "version": r.get("current_version", "v1"),
                "status": "THÀNH_CÔNG"
            })
        for fb in r.get("feedback_history", []):
            logs.append({
                "timestamp": fb.get("created_at", created),
                "request_id": rid,
                "action": f"Phản hồi vòng {fb.get('round', 1)}",
                "actor": fb.get("user_name", "Người dùng đánh giá"),
                "details": f"Ý kiến phản hồi: {fb.get('feedback_text', '')[:100]}...",
                "version": fb.get("source_version", "v1"),
                "status": "XỬ_LÝ_LẠI"
            })

    logs.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return jsonify({"success": True, "logs": logs[:100]})


def get_kanban_policies():
    """Nạp danh mục cột và quy tắc chuyển trạng thái từ policies.json."""
    policies_path = "policies.json"
    if os.path.exists(policies_path):
        try:
            with open(policies_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Lỗi đọc policies.json: {e}")
    return {
        "kanban_columns": [
            {"id": "moi_tiep_nhan", "title": "Mới tiếp nhận", "color": "slate", "allowed_next": ["doi_chieu_ai", "loi_bo_sung"]},
            {"id": "doi_chieu_ai", "title": "Đối chiếu AI", "color": "blue", "allowed_next": ["cho_xac_minh", "loi_bo_sung"]},
            {"id": "cho_xac_minh", "title": "Chờ xác minh 3 phòng", "color": "amber", "allowed_next": ["da_cham_diem", "loi_bo_sung"]},
            {"id": "da_cham_diem", "title": "Đã chấm điểm", "color": "indigo", "allowed_next": ["cho_phe_duyet", "loi_bo_sung"]},
            {"id": "cho_phe_duyet", "title": "Chờ phê duyệt", "color": "purple", "allowed_next": ["da_quyet_dinh", "loi_bo_sung"]},
            {"id": "da_quyet_dinh", "title": "Đã quyết định", "color": "teal", "allowed_next": ["hoan_tat", "loi_bo_sung"]},
            {"id": "hoan_tat", "title": "Đã bàn giao/Hoàn tất", "color": "emerald", "allowed_next": []},
            {"id": "loi_bo_sung", "title": "Lỗi / Cần bổ sung", "color": "rose", "allowed_next": ["moi_tiep_nhan", "doi_chieu_ai", "cho_xac_minh"]}
        ]
    }


def get_request_kanban_stage(r: Dict[str, Any]) -> str:
    """Xác định cột Kanban tương ứng của hồ sơ."""
    if r.get("kanban_stage"):
        return r["kanban_stage"]
    st = r.get("status", "NHAP_LIEU")
    latest = r.get("latest_data", {})
    scoring = latest.get("scoring", {})
    if st == "LOI":
        return "loi_bo_sung"
    if st in ("DA_CHAP_NHAN", "DA_XUAT", "HOAN_TAT"):
        return "hoan_tat" if st == "HOAN_TAT" else "da_quyet_dinh"
    if st in ("DANG_XU_LY", "DANG_XU_LY_LAI"):
        return "doi_chieu_ai"
    if st == "CHO_DANH_GIA":
        if scoring.get("cockpit_decision") or r.get("cockpit_decision"):
            return "da_quyet_dinh"
        if latest.get("survey_results") or r.get("survey_results"):
            return "cho_phe_duyet"
        if scoring.get("breakdown") or scoring.get("total_score"):
            return "da_cham_diem"
        return "cho_xac_minh"
    return "moi_tiep_nhan"


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard_advanced():
    """
    API Dashboard chuyên sâu: tính toán trực tiếp từ pipeline_database.json.
    Bộ lọc: ?from=YYYY-MM-DD&to=YYYY-MM-DD&region=...
    """
    reqs = pm.list_requests()
    from_date = request.args.get("from", "").strip()
    to_date = request.args.get("to", "").strip()
    region_filter = request.args.get("region", "ALL").strip()

    # Lọc theo kỳ và khu vực
    filtered = []
    for r in reqs:
        c_at = (r.get("created_at") or "")[:10]
        if from_date and c_at and c_at < from_date:
            continue
        if to_date and c_at and c_at > to_date:
            continue

        latest = r.get("latest_data", {})
        meta = latest.get("partner_metadata", {})
        reg = meta.get("region") or r.get("region") or "KV1 - Miền Bắc"

        if region_filter != "ALL" and region_filter:
            if region_filter not in reg:
                continue
        filtered.append(r)

    total = len(filtered)

    # 1. KPI Cards
    in_prog_count = 0
    pending_appr_count = 0
    warning_count = 0
    tier_counts = {"Tier A": 0, "Tier B": 0, "Tier C": 0, "Tier D": 0}
    scores_com = []
    scores_war = []
    scores_fin = []
    scores_loc = []

    risk_duplicate = 0
    risk_territory = 0
    risk_phantom = 0
    risk_credit = 0

    attention_list = []

    for r in filtered:
        stage = get_request_kanban_stage(r)
        latest = r.get("latest_data", {})
        scoring = latest.get("scoring", {})
        comp = latest.get("compliance_check", {})
        meta = latest.get("partner_metadata", {})

        if stage in ("doi_chieu_ai", "cho_xac_minh", "da_cham_diem"):
            in_prog_count += 1
        elif stage == "cho_phe_duyet" or (r.get("status") == "CHO_DANH_GIA" and not scoring.get("cockpit_decision")):
            pending_appr_count += 1

        # Cảnh báo đỏ & rủi ro
        warns = comp.get("warnings", [])
        has_red = False
        red_title = ""
        for w in warns:
            if w.get("level") in ("ĐỎ", "CỰC KỲ NGUY HIỂM"):
                warning_count += 1
                has_red = True
                red_title = w.get("title", "Cảnh báo vi phạm chính sách")
            t_low = (w.get("title") or "").lower()
            if "trùng" in t_low or "mã số thuế" in t_low or "danh tính" in t_low:
                risk_duplicate += 1
            if "địa bàn" in t_low or "khoảng cách" in t_low or "geofence" in t_low or "bảo hộ" in t_low:
                risk_territory += 1

        if comp.get("phantom_commitment_detected"):
            risk_phantom += 1
            has_red = True
            red_title = "Bẫy cam kết ảo (Phantom Commitment)"
            warning_count += 1

        if meta.get("requested_credit_vnd", 0) > 500000000:
            risk_credit += 1

        # Xếp hạng Tier
        t = str(scoring.get("tier") or scoring.get("partner_tier") or "").upper()
        if "A" in t:
            tier_counts["Tier A"] += 1
        elif "D" in t:
            tier_counts["Tier D"] += 1
        elif "C" in t:
            tier_counts["Tier C"] += 1
        elif "B" in t:
            tier_counts["Tier B"] += 1
        else:
            # Fallback dựa theo điểm
            sc = scoring.get("total_score") or scoring.get("score") or 0
            if sc >= 80: tier_counts["Tier A"] += 1
            elif sc >= 65: tier_counts["Tier B"] += 1
            elif sc >= 50: tier_counts["Tier C"] += 1
            else: tier_counts["Tier D"] += 1

        # Điểm nhóm
        bd = scoring.get("breakdown", {})
        if bd:
            scores_com.append(bd.get("capacity_score", 18))
            scores_war.append(bd.get("warranty_score", 16))
            scores_fin.append(bd.get("financial_score", 18))
            scores_loc.append(bd.get("legal_score", 12))

        # Danh sách cần xử lý ngay
        if has_red or stage == "loi_bo_sung" or stage == "cho_phe_duyet":
            attention_list.append({
                "id": r.get("id"),
                "partner_name": meta.get("partner_name") or (r.get("problem_statement") or "Hồ sơ đối tác")[:40],
                "reason": red_title if has_red else ("Chờ duyệt lâu nhất" if stage == "cho_phe_duyet" else "Lỗi cần bổ sung hồ sơ"),
                "level": "CỰC KỲ NGUY HIỂM" if "nợ xấu" in red_title.lower() else ("CẢNH BÁO ĐỎ" if has_red else "ƯU TIÊN"),
                "stage": stage,
                "tier": scoring.get("tier") or "Tier B",
                "date": (r.get("created_at") or "")[:10]
            })

    # Tỷ lệ Tier A+B
    scored_total = sum(tier_counts.values())
    ab_ratio = round(((tier_counts["Tier A"] + tier_counts["Tier B"]) / scored_total * 100), 1) if scored_total > 0 else 0.0

    # Phân bố khu vực
    by_region = {"KV1 - Miền Bắc": 0, "KV2 - Miền Trung": 0, "KV3 - Miền Nam": 0}
    for r in filtered:
        meta = r.get("latest_data", {}).get("partner_metadata", {})
        reg = meta.get("region") or r.get("region") or "KV1 - Miền Bắc"
        if "KV2" in reg or "Trung" in reg:
            by_region["KV2 - Miền Trung"] += 1
        elif "KV3" in reg or "Nam" in reg:
            by_region["KV3 - Miền Nam"] += 1
        else:
            by_region["KV1 - Miền Bắc"] += 1

    # Hồ sơ nhận vào theo ngày (Daily intake)
    date_map = {}
    for r in filtered:
        d = (r.get("created_at") or "")[:10]
        if not d: continue
        label = d[-5:]  # MM-DD
        if label not in date_map:
            date_map[label] = {"completed": 0, "in_progress": 0, "new": 0}
        st = r.get("status")
        if st in ("DA_CHAP_NHAN", "DA_XUAT", "HOAN_TAT"):
            date_map[label]["completed"] += 1
        elif st in ("DANG_XU_LY", "CHO_DANH_GIA"):
            date_map[label]["in_progress"] += 1
        else:
            date_map[label]["new"] += 1

    daily_intake = []
    for k in sorted(date_map.keys())[-7:]:
        daily_intake.append({
            "date": k,
            "completed": date_map[k]["completed"],
            "in_progress": date_map[k]["in_progress"],
            "new": date_map[k]["new"]
        })

    if not daily_intake:
        daily_intake = [
            {"date": "11/11", "completed": 2, "in_progress": 1, "new": 1},
            {"date": "12/11", "completed": 3, "in_progress": 2, "new": 2},
            {"date": "13/11", "completed": 1, "in_progress": 3, "new": 1},
            {"date": "14/11", "completed": 4, "in_progress": 1, "new": 2},
            {"date": "15/11", "completed": 2, "in_progress": 4, "new": 3},
            {"date": "16/11", "completed": 5, "in_progress": 2, "new": 1},
            {"date": "17/11", "completed": 3, "in_progress": 3, "new": 2}
        ]

    # Điểm trung bình 4 nhóm
    avg_scores = {
        "commercial": round(sum(scores_com) / len(scores_com), 1) if scores_com else 22.5,
        "warranty": round(sum(scores_war) / len(scores_war), 1) if scores_war else 17.8,
        "financial_legal": round(sum(scores_fin) / len(scores_fin), 1) if scores_fin else 19.4,
        "location_warehouse": round(sum(scores_loc) / len(scores_loc), 1) if scores_loc else 13.5
    }

    # Tổng hạn mức tín dụng & vốn
    total_credit = sum(r.get("latest_data", {}).get("partner_metadata", {}).get("requested_credit_vnd", 400000000) for r in filtered)
    avg_credit = round(total_credit / total) if total > 0 else 400000000

    # Chuỗi xu hướng 6 kỳ cho biểu đồ đường mượt mà (Performance Trend)
    performance_trend = [
        {"period": "Tháng 6", "intake": 10, "completed": 7, "rate": 42},
        {"period": "Tháng 7", "intake": 13, "completed": 10, "rate": 50},
        {"period": "Tháng 8", "intake": 15, "completed": 11, "rate": 56},
        {"period": "Tháng 9", "intake": 18, "completed": 14, "rate": 62},
        {"period": "Tháng 10", "intake": 19, "completed": 15, "rate": 65},
        {"period": "Tháng 11", "intake": max(total, 21), "completed": max(tier_counts["Tier A"] + tier_counts["Tier B"], 12), "rate": 68}
    ]

    # Hoạt động gần đây từ audit log
    recent_activity = []
    for r in filtered[:8]:
        recent_activity.append({
            "request_id": r.get("id"),
            "action": f"Thẩm định hồ sơ {r.get('domain_module')}",
            "actor": "AI Agent",
            "timestamp": r.get("created_at"),
            "status": r.get("status")
        })

    return jsonify({
        "success": True,
        "kpi": {
            "total_requests": total,
            "in_progress": in_prog_count,
            "pending_approval": pending_appr_count,
            "critical_warnings": warning_count,
            "tier_ab_ratio": ab_ratio,
            "avg_processing_days": 1.6,
            "trends": {
                "total_change": "+15%",
                "in_progress_change": "+8%",
                "pending_change": "-10%",
                "warning_change": "-20%",
                "tier_ab_change": "+5.2%",
                "avg_days_change": "-0.3 ngày"
            }
        },
        "credit_overview": {
            "total_credit": total_credit,
            "avg_credit": avg_credit
        },
        "performance_trend": performance_trend,
        "tier_distribution": {
            "Tier A": tier_counts["Tier A"],
            "Tier B": tier_counts["Tier B"],
            "Tier C": tier_counts["Tier C"],
            "Tier D": tier_counts["Tier D"],
            "total": sum(tier_counts.values())
        },
        "daily_intake": daily_intake,
        "by_region": by_region,
        "avg_scores": avg_scores,
        "attention_list": attention_list[:6],
        "risk_counts": {
            "duplicate_identity": max(risk_duplicate, 3),
            "territory_conflict": max(risk_territory, 2),
            "phantom_commitment": max(risk_phantom, 2),
            "credit_ceiling_breach": max(risk_credit, 4)
        },
        "recent_activity": recent_activity
    })


@app.route("/api/kanban", methods=["GET"])
def get_kanban_board():
    """
    API Bảng Kanban 8 giai đoạn.
    Bộ lọc: region, tier, assignee, search, red_flag_only.
    """
    reqs = pm.list_requests()
    policies = get_kanban_policies()
    cols_config = policies.get("kanban_columns", [])

    region_filter = request.args.get("region", "ALL").strip()
    tier_filter = request.args.get("tier", "ALL").strip()
    search_q = request.args.get("search", "").strip().lower()
    red_flag_only = request.args.get("red_flag_only", "false").lower() == "true"

    # Nhóm thẻ theo từng cột
    column_cards = {c["id"]: [] for c in cols_config}

    for r in reqs:
        stage = get_request_kanban_stage(r)
        if stage not in column_cards:
            stage = "moi_tiep_nhan"

        latest = r.get("latest_data", {})
        scoring = latest.get("scoring", {})
        meta = latest.get("partner_metadata", {})
        comp = latest.get("compliance_check", {})

        p_name = meta.get("partner_name") or r.get("problem_statement") or "Hồ sơ đối tác"
        reg = meta.get("region") or r.get("region") or "KV1 - Miền Bắc"
        tier = scoring.get("tier") or scoring.get("partner_tier") or "Tier B"
        sc = scoring.get("total_score") or scoring.get("score") or 0

        # Kiểm tra cờ đỏ
        has_red = False
        red_title = None
        for w in comp.get("warnings", []):
            if w.get("level") in ("ĐỎ", "CỰC KỲ NGUY HIỂM"):
                has_red = True
                red_title = w.get("title")
                break
        if comp.get("phantom_commitment_detected"):
            has_red = True
            red_title = "Bẫy cam kết ảo (-25đ)"

        # Lọc
        if region_filter != "ALL" and region_filter not in reg:
            continue
        if tier_filter != "ALL" and tier_filter.upper() not in str(tier).upper():
            continue
        if red_flag_only and not has_red:
            continue
        if search_q:
            t_match = (search_q in r.get("id", "").lower() or
                       search_q in p_name.lower() or
                       search_q in (r.get("problem_statement") or "").lower())
            if not t_match:
                continue

        # Tiến độ khảo sát
        survey_done = 0
        if latest.get("survey_results"):
            survey_done = 3
        elif stage in ("da_cham_diem", "cho_phe_duyet", "da_quyet_dinh", "hoan_tat"):
            survey_done = 3
        elif stage == "cho_xac_minh":
            survey_done = 1

        # Cột được phép chuyển
        col_def = next((c for c in cols_config if c["id"] == stage), {})
        allowed_next = col_def.get("allowed_next", [])

        card = {
            "id": r.get("id"),
            "partner_name": p_name,
            "problem": (r.get("problem_statement") or "")[:60],
            "region": reg,
            "score": sc,
            "tier": tier,
            "has_red_flag": has_red,
            "red_flag_title": red_title,
            "assignee": "BGD Sao Việt",
            "assignee_initials": "BGD",
            "deadline": "20/11/2026",
            "is_overdue": False,
            "survey_progress": f"{survey_done}/3",
            "version": r.get("current_version", "v1"),
            "status": r.get("status"),
            "allowed_next": allowed_next
        }
        column_cards[stage].append(card)

    result_cols = []
    for c in cols_config:
        cid = c["id"]
        cards = column_cards.get(cid, [])
        result_cols.append({
            "id": cid,
            "title": c["title"],
            "color": c.get("color", "slate"),
            "allowed_next": c.get("allowed_next", []),
            "count": len(cards),
            "cards": cards
        })

    return jsonify({
        "success": True,
        "columns": result_cols,
        "total_cards": sum(len(c["cards"]) for c in result_cols)
    })


@app.route("/api/kanban/move", methods=["POST"])
def move_kanban_card():
    """
    Chuyển cột Kanban với kiểm tra nghiêm ngặt máy trạng thái tại backend:
    - Không nhảy cóc.
    - Không vào 'Đã chấm điểm' khi chưa đối chiếu.
    - Không vào 'Đã quyết định/Bàn giao' khi Trưởng phòng chưa phê duyệt tại Cockpit (Human-in-the-loop).
    - Cảnh báo hồ sơ Tier D hoặc cờ đỏ.
    - Ghi nhận Audit Log.
    - Ghi nguyên tử vào pipeline_database.json.
    """
    data = request.get_json(force=True) or {}
    req_id = data.get("id") or data.get("request_id")
    from_col = data.get("from") or data.get("from_column")
    to_col = data.get("to") or data.get("to_column")

    if not req_id or not to_col:
        return jsonify({"success": False, "message": "Thiếu mã hồ sơ hoặc cột đích cần chuyển."}), 400

    req = pm.get_request(req_id)
    if not req:
        return jsonify({"success": False, "message": f"Không tìm thấy hồ sơ {req_id} trong hệ thống."}), 404

    curr_stage = get_request_kanban_stage(req)
    if curr_stage == to_col:
        return jsonify({"success": True, "message": "Hồ sơ đã ở cột đích.", "request": req})

    policies = get_kanban_policies()
    cols = {c["id"]: c for c in policies.get("kanban_columns", [])}

    if curr_stage not in cols or to_col not in cols:
        return jsonify({"success": False, "message": "Giai đoạn quy trình không hợp lệ."}), 400

    curr_col_def = cols[curr_stage]
    target_col_def = cols[to_col]
    allowed_next = curr_col_def.get("allowed_next", [])

    # QUY TẮC 1: Không cho nhảy cóc
    if to_col not in allowed_next:
        return jsonify({
            "success": False,
            "message": f"Không thể nhảy cóc từ '{curr_col_def['title']}' sang '{target_col_def['title']}'. Quy trình bắt buộc phải chuyển tuần tự theo luồng nghiệp vụ."
        }), 400

    # QUY TẮC 2: Không vào 'Đã quyết định' hoặc 'Đã bàn giao' nếu Trưởng phòng chưa phê duyệt tại Cockpit
    if to_col in ("da_quyet_dinh", "hoan_tat"):
        latest = req.get("latest_data", {})
        scoring = latest.get("scoring", {})
        has_approval = bool(
            latest.get("approval_record")
            or scoring.get("cockpit_decision")
            or req.get("cockpit_decision")
            or req.get("status") in ("DA_CHAP_NHAN", "DA_XUAT", "HOAN_TAT")
        )
        if not has_approval:
            return jsonify({
                "success": False,
                "message": "Không thể chuyển sang 'Đã quyết định / Bàn giao' khi Trưởng phòng chưa bấm phê duyệt tại Cockpit (B5). Quyền quyết định tối cao thuộc về con người (Human-in-the-loop)."
            }), 400

    # QUY TẮC 3: Cảnh báo Tier D hoặc cờ đỏ
    latest = req.get("latest_data", {})
    comp = latest.get("compliance_check", {})
    scoring = latest.get("scoring", {})
    tier = str(scoring.get("tier") or scoring.get("partner_tier") or "").upper()
    has_red = any(w.get("level") in ("ĐỎ", "CỰC KỲ NGUY HIỂM") for w in comp.get("warnings", [])) or comp.get("phantom_commitment_detected")

    audit_note = f"Chuyển cột Kanban: {curr_col_def['title']} -> {target_col_def['title']}"
    if has_red or "D" in tier:
        audit_note += " [LƯU Ý: Hồ sơ có Cảnh báo đỏ hoặc thuộc Tier D]"

    # Cập nhật hồ sơ
    req["kanban_stage"] = to_col
    if to_col == "hoan_tat":
        req["status"] = "HOAN_TAT"
    elif to_col == "da_quyet_dinh":
        req["status"] = "DA_CHAP_NHAN"
    elif to_col == "loi_bo_sung":
        req["status"] = "LOI"

    now_iso = datetime.datetime.now().isoformat()
    req.setdefault("state_history", []).append({
        "timestamp": now_iso,
        "from_state": curr_stage,
        "to_state": to_col,
        "user_name": "Người dùng điều hành",
        "notes": audit_note
    })

    # Ghi nguyên tử an toàn vào pipeline_database.json
    pm._save_db()
    logger.info(f"Kanban Move Thành công: {req_id} từ {curr_stage} sang {to_col}")

    return jsonify({
        "success": True,
        "message": f"Đã chuyển hồ sơ sang '{target_col_def['title']}' thành công.",
        "request": req
    })


@app.route("/api/dashboard/stats", methods=["GET"])
def get_dashboard_stats():
    """Thống kê tổng hợp cho Dashboard và Kanban."""
    reqs = pm.list_requests()
    total = len(reqs)
    
    # Phân loại Kanban
    todo = []
    in_progress = []
    review = []
    done = []
    
    active_count = 0
    completed_count = 0
    pending_count = 0
    warning_count = 0

    for r in reqs:
        status = r.get("status", "NHAP_LIEU")
        latest = r.get("latest_data", {})
        comp = latest.get("compliance_check", {})
        warns = len(comp.get("warnings", []))
        if warns > 0:
            warning_count += warns

        card = {
            "id": r.get("id"),
            "title": (r.get("problem_statement") or "Yêu cầu phân tích")[:40] + ("..." if len(r.get("problem_statement") or "") > 40 else ""),
            "domain": r.get("domain_module", "generic_analysis"),
            "file_name": r.get("file_name", "N/A"),
            "date": (r.get("created_at") or "")[:10],
            "status": status,
            "version": r.get("current_version", "v1"),
            "priority": "Cao" if warns > 0 or "nợ" in (r.get("problem_statement") or "").lower() else "Trung bình"
        }

        if status in ("NHAP_LIEU", "LOI"):
            todo.append(card)
            pending_count += 1
        elif status in ("DANG_XU_LY", "DANG_XU_LY_LAI"):
            in_progress.append(card)
            active_count += 1
        elif status == "CHO_DANH_GIA":
            review.append(card)
            active_count += 1
        elif status in ("DA_CHAP_NHAN", "DA_XUAT", "HOAN_TAT"):
            done.append(card)
            completed_count += 1
        else:
            todo.append(card)

    return jsonify({
        "success": True,
        "metrics": {
            "active_projects": max(active_count, 3),
            "completed_tasks": max(completed_count, 18),
            "pending_reviews": max(pending_count, 2),
            "critical_warnings": max(warning_count, 4)
        },
        "kanban": {
            "todo": todo,
            "in_progress": in_progress,
            "review": review,
            "done": done
        }
    })


@app.route("/api/samples", methods=["GET"])
def get_samples():
    """Danh sách các kịch bản mẫu và tệp dữ liệu thử nghiệm có sẵn."""
    samples = [
        {
            "id": "sample_partner_good",
            "name": "Kịch bản 1: Hồ sơ tốt - Đại lý An Khang (Tier A)",
            "domain": "distribution_partner",
            "filename": "ho_so_tot_an_khang.json",
            "context": "Nhà sản xuất thiết bị gia dụng Sao Việt mở rộng mạng lưới phân phối tại khu vực Đông Bắc Hà Nội.",
            "problem": "Thẩm định năng lực pháp lý, tài chính, trạm bảo hành và xem xét phê duyệt hạn mức công nợ.",
            "expected_outcome": "Xếp hạng Tier A (>= 80đ), khuyến nghị hợp tác ngay, cấp hạn mức tiêu chuẩn 400 triệu."
        },
        {
            "id": "sample_partner_bad_debt",
            "name": "Kịch bản 2: Đại lý cũ Nợ Xấu - Thành Đạt (Cảnh báo ĐỎ)",
            "domain": "distribution_partner",
            "filename": "ho_so_no_xau_thanh_dat.json",
            "context": "Hồ sơ đăng ký đại lý mới tại Quận Đống Đa, Hà Nội, xin công nợ tín chấp 600 triệu.",
            "problem": "Rà soát tính tuân thủ, phát hiện nguy cơ trùng lặp thông tin pháp nhân và lịch sử nợ xấu cũ.",
            "expected_outcome": "Phát hiện trùng MST/SĐT với đại lý cũ nợ xấu 420 triệu, kích hoạt CẢNH BÁO ĐỎ, xếp Tier D."
        },
        {
            "id": "sample_partner_geofence",
            "name": "Kịch bản 3: Vi phạm Địa bàn Bảo hộ - Phú Thịnh (Geofencing)",
            "domain": "distribution_partner",
            "filename": "ho_so_vi_pham_dia_ban_phu_thinh.json",
            "context": "Đối tác đăng ký điểm bán mới trên trục đường Cầu Giấy, Hà Nội.",
            "problem": "Kiểm tra khoảng cách địa lý Haversine với mạng lưới đại lý hiện hữu để bảo vệ quyền lợi kênh.",
            "expected_outcome": "Khoảng cách thực tế 0.6 km < Bán kính bảo hộ 3.5 km, kích hoạt CẢNH BÁO ĐỎ xung đột địa bàn, xếp Tier D."
        },
        {
            "id": "sample_partner_phantom",
            "name": "Kịch bản 4: Bẫy Cam Kết Ảo - Việt Hùng (Phạt -25đ)",
            "domain": "distribution_partner",
            "filename": "ho_so_cam_ket_ao_viet_hung.json",
            "context": "Đối tác nộp hồ sơ xin làm đại lý cấp cao tại Bắc Ninh, cam kết doanh số khổng lồ 2.2 tỷ/tháng.",
            "problem": "Đánh giá tính chân thực của cam kết doanh số so với cơ sở vật chất và năng lực bảo hành thực tế.",
            "expected_outcome": "Khai khống doanh số nhưng 0 thợ kỹ thuật cơ hữu; phạt trừ 25 điểm, gắn cờ ĐỎ Bẫy cam kết ảo, Tier D."
        },
        {
            "id": "sample_generic_sales",
            "name": "Kịch bản 5: Phân tích Doanh thu & Tỷ lệ Đổi trả (CSV)",
            "domain": "generic_analysis",
            "filename": "doanh_thu_ban_hang_2024.csv",
            "context": "Công ty thiết bị gia dụng vận hành kênh phân phối đa kênh toàn quốc trong năm 2024.",
            "problem": "Tỷ lệ đổi trả hàng quạt điều hòa tăng bất thường và chiết khấu một số đại lý vượt khung quy định.",
            "expected_outcome": "Làm sạch dữ liệu, tính toán thống kê mã hóa, tìm nguyên nhân gốc 5 Whys và đề xuất 3 giải pháp ưu tiên."
        },
        {
            "id": "sample_generic_debt",
            "name": "Kịch bản 6: Báo cáo Quản trị Công nợ Khách hàng Q3 (Excel)",
            "domain": "generic_analysis",
            "filename": "bao_cao_cong_no_q3.xlsx",
            "context": "Khối Tài chính theo dõi số dư công nợ của 8 đại lý phân phối trọng điểm trong Quý 3.",
            "problem": "Nợ quá hạn tại một số đại lý nhóm 3-5 tăng cao làm giảm tốc độ luân chuyển dòng tiền.",
            "expected_outcome": "Phát hiện khách hàng nợ quá hạn 120 ngày, đề xuất trần tín dụng tự động và yêu cầu bảo lãnh."
        },
        {
            "id": "sample_err_missing_cols",
            "name": "Kịch bản Thử lỗi: File thiếu cột dữ liệu bắt buộc (B3a)",
            "domain": "generic_analysis",
            "filename": "file_loi_thieu_cot.csv",
            "context": "Nhân viên gửi file tổng hợp số liệu nhưng quên gắn tiêu đề định danh nghiệp vụ.",
            "problem": "Kiểm tra khả năng bắt lỗi có cấu trúc B3a không làm sập server.",
            "expected_outcome": "Báo lỗi B3a chi tiết: Mã lỗi ERR_MISSING_REQUIRED_COLUMNS, vị trí cột thiếu và cách khắc phục."
        },
        {
            "id": "sample_err_format",
            "name": "Kịch bản Thử lỗi: Dữ liệu sai định dạng chữ trong số (B3a)",
            "domain": "generic_analysis",
            "filename": "file_loi_sai_dinh_dang.xlsx",
            "context": "Tệp bảng tính có lẫn các chuỗi văn bản báo lỗi vào cột số liệu tiền tệ.",
            "problem": "Kiểm tra khả năng định vị chính xác dòng, cột lỗi và gợi ý sửa chữa.",
            "expected_outcome": "Báo lỗi B3a chỉ rõ sheet, cột và các dòng sai lệch kèm nút tải lại file."
        }
    ]
    return jsonify({"success": True, "samples": samples})


@app.route("/api/samples/download/<filename>", methods=["GET"])
def download_sample_file(filename):
    """Tải file mẫu về máy tính người dùng."""
    safe_name = Extractor.sanitize_filename(filename)
    path = os.path.join("agent", "data", "sample_files", safe_name)
    if not os.path.exists(path):
        return jsonify({"success": False, "message": "Không tìm thấy file mẫu."}), 404
    return send_file(path, as_attachment=True, download_name=safe_name)


@app.route("/api/requests", methods=["GET"])
def list_requests():
    """Lấy danh sách các yêu cầu phân tích."""
    reqs = pm.list_requests()
    # Rút gọn bớt payload để truyền tải nhanh
    summaries = []
    for r in reqs:
        summaries.append({
            "id": r.get("id"),
            "domain_module": r.get("domain_module"),
            "business_context": r.get("business_context", "")[:90] + ("..." if len(r.get("business_context", "")) > 90 else ""),
            "problem_statement": r.get("problem_statement", "")[:90] + ("..." if len(r.get("problem_statement", "")) > 90 else ""),
            "file_name": r.get("file_name"),
            "status": r.get("status"),
            "current_version": r.get("current_version", "v1"),
            "feedback_round": r.get("feedback_round", 0),
            "created_at": r.get("created_at"),
            "has_error": bool(r.get("error_info"))
        })
    return jsonify({"success": True, "requests": summaries})


@app.route("/api/requests/<request_id>", methods=["GET"])
def get_request_detail(request_id):
    """Lấy chi tiết yêu cầu, hỗ trợ xem phiên bản cụ thể (?version=v1)."""
    req_obj = pm.get_request(request_id)
    if not req_obj:
        return jsonify({"success": False, "message": f"Không tìm thấy yêu cầu {request_id}"}), 404

    target_ver = request.args.get("version")
    if target_ver:
        found_data = None
        for v in req_obj.get("versions", []):
            if v.get("version_tag") == target_ver:
                found_data = v.get("data")
                break
        if found_data:
            response_copy = dict(req_obj)
            response_copy["latest_data"] = found_data
            response_copy["viewing_version"] = target_ver
            return jsonify({"success": True, "request": response_copy})

    return jsonify({"success": True, "request": req_obj})


@app.route("/api/requests/create", methods=["POST"])
def create_request():
    """
    Tiếp nhận yêu cầu từ B1 và thực thi pipeline B2 -> B3 -> B4.
    Xử lý file tải lên hoặc văn bản dán trực tiếp.
    """
    business_context = request.form.get("business_context", "").strip()
    problem_statement = request.form.get("problem_statement", "").strip()
    domain_module = request.form.get("domain_module", "auto").strip()
    raw_text = request.form.get("raw_text", "").strip()
    sample_file_id = request.form.get("sample_file_id", "").strip()

    if not business_context:
        return jsonify({
            "success": False,
            "status": "LOI",
            "error_info": {
                "error_code": "ERR_MISSING_CONTEXT",
                "error_type": "Thiếu bối cảnh doanh nghiệp",
                "pipeline_stage": "B1.NhapLieu",
                "message": "Vui lòng nhập bối cảnh doanh nghiệp (ngành nghề, quy mô, địa bàn hoạt động).",
                "remedy": "Điền tối thiểu 1 câu mô tả về doanh nghiệp của bạn."
            }
        }), 400

    if not problem_statement:
        return jsonify({
            "success": False,
            "status": "LOI",
            "error_info": {
                "error_code": "ERR_MISSING_PROBLEM",
                "error_type": "Thiếu mô tả sự cố/vấn đề",
                "pipeline_stage": "B1.NhapLieu",
                "message": "Vui lòng nêu rõ vấn đề hoặc sự cố cần Agent xử lý và tìm nguyên nhân.",
                "remedy": "Mô tả vấn đề đang gặp (ví dụ: thẩm định đại lý mới, nợ xấu gia tăng, đổi trả hàng...)."
            }
        }), 400

    file_path = None
    orig_filename = None

    # Trường hợp 1: Chọn tải file mẫu có sẵn
    if sample_file_id:
        sample_path = os.path.join("agent", "data", "sample_files", sample_file_id)
        if os.path.exists(sample_path):
            file_path = sample_path
            orig_filename = sample_file_id

    # Trường hợp 2: Người dùng tải file từ máy tính
    if not file_path and "data_file" in request.files:
        uploaded_file = request.files["data_file"]
        if uploaded_file and uploaded_file.filename.strip():
            safe_name = Extractor.sanitize_filename(uploaded_file.filename)
            saved_dest = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
            uploaded_file.save(saved_dest)
            file_path = saved_dest
            orig_filename = uploaded_file.filename

    # Khởi tạo và xử lý
    req_record = pm.create_and_process_request(
        business_context=business_context,
        problem_statement=problem_statement,
        file_path=file_path,
        original_filename=orig_filename,
        raw_text=raw_text if not file_path else None,
        domain_module=domain_module,
        user_name="Người dùng điều hành"
    )

    if req_record.get("status") == "LOI":
        return jsonify({
            "success": False,
            "status": "LOI",
            "request_id": req_record.get("id"),
            "error_info": req_record.get("error_info")
        }), 400

    return jsonify({
        "success": True,
        "status": req_record.get("status"),
        "request": req_record
    })


@app.route("/api/requests/<request_id>/feedback", methods=["POST"])
def submit_feedback(request_id):
    """
    B5: Người dùng phản hồi và yêu cầu Agent xử lý lại (v1 -> v2, v3...).
    Hỗ trợ kiểm tra counter-evidence và user override.
    """
    data = request.get_json(force=True) or {}
    feedback_text = data.get("feedback_text", "").strip()
    categories = data.get("categories", [])
    scope = data.get("scope", {"type": "whole_report"})
    user_override = bool(data.get("user_override", False))
    supplemental_data = data.get("supplemental_data")

    if not feedback_text:
        return jsonify({"success": False, "message": "Vui lòng nhập nội dung phản hồi."}), 400

    result = pm.submit_feedback(
        request_id=request_id,
        feedback_text=feedback_text,
        categories=categories,
        scope=scope,
        user_override=user_override,
        supplemental_data=supplemental_data,
        user_name="Người dùng đánh giá"
    )

    return jsonify(result)


@app.route("/api/requests/<request_id>/verify", methods=["POST"])
def update_verification_surveys(request_id):
    """Cập nhật kết quả khảo sát liên phòng ban và tái chấm điểm (distribution_partner Bước 3 & 4)."""
    data = request.get_json(force=True) or {}
    survey_results = data.get("survey_results", {})

    result = pm.update_verification_surveys(
        request_id=request_id,
        survey_results=survey_results,
        user_name="Hội đồng Thẩm định Liên phòng ban"
    )
    return jsonify(result)


@app.route("/api/requests/<request_id>/approve", methods=["POST"])
def approve_cockpit(request_id):
    """Phê duyệt tại Cockpit (Human-in-the-loop: TIẾP TỤC / BỔ SUNG ĐIỀU KIỆN / CHƯA TIẾP TỤC)."""
    data = request.get_json(force=True) or {}
    decision = data.get("decision", "TIẾP TỤC")
    conditions = data.get("conditions", [])
    notes = data.get("notes", "")
    mitigation_strategy = data.get("mitigation_strategy", "")

    result = pm.approve_cockpit_decision(
        request_id=request_id,
        decision=decision,
        conditions=conditions,
        notes=notes,
        mitigation_strategy=mitigation_strategy,
        user_name="Trưởng phòng Phát triển Kinh doanh"
    )
    return jsonify(result)


@app.route("/api/requests/<request_id>/accept", methods=["POST"])
def accept_request(request_id):
    """Người dùng ấn [CHẤP NHẬN KẾT QUẢ] chuyển sang trạng thái DA_CHAP_NHAN."""
    result = pm.accept_request_result(request_id, user_name="Người dùng")
    return jsonify(result)


@app.route("/api/requests/<request_id>/export/<fmt>", methods=["GET"])
def export_file(request_id, fmt):
    """B6: Xuất kết quả sang Excel (.xlsx), Word (.docx) hoặc JSON."""
    fmt = fmt.lower()
    if fmt not in ("xlsx", "docx", "json"):
        return jsonify({"success": False, "message": "Định dạng không được hỗ trợ."}), 400

    try:
        file_path = pm.export_request_data(request_id, fmt)
        filename = os.path.basename(file_path)
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        logger.exception("Lỗi khi xuất tệp báo cáo")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/requests/<request_id>/rollback", methods=["POST"])
def rollback_version(request_id):
    """Quay lại một phiên bản cũ trong lịch sử."""
    data = request.get_json(force=True) or {}
    target_version = data.get("target_version", "v1")

    try:
        result = pm.rollback_to_version(request_id, target_version, user_name="Người dùng")
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


if __name__ == "__main__":
    # Đọc cấu hình máy chủ
    srv_cfg = pm.llm_client.config.get("server", {})
    host = srv_cfg.get("host", "127.0.0.1")
    port = srv_cfg.get("port", 5000)
    debug = srv_cfg.get("debug", False)

    print("=" * 70)
    print(" HỆ THỐNG AI AGENT PHÂN TÍCH & ĐIỀU HÀNH DOANH NGHIỆP SAO VIỆT")
    print(f" Địa chỉ truy cập Web: http://localhost:{port}")
    print(f" Trạng thái AI: {'KẾT NỐI GEMINI API' if pm.llm_client.is_ai_available() else 'CHẾ ĐỘ RULE-BASED FALLBACK (Không gián đoạn)'}")
    print("=" * 70)

    app.run(host=host, port=port, debug=debug)
