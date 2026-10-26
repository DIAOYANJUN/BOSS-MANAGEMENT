import streamlit as st
import pandas as pd
import json
import base64
import requests
import os
from datetime import datetime

# ---------------- 0. 页面配置 ----------------
st.set_page_config(
    page_title="小店智能备忘录与协同系统",
    page_icon="📋",
    layout="wide"
)

DATA_FILE = "memos.json"

# ---------------- 1. 极速双向同步与诊断机制 ----------------
def get_github_config():
    try:
        gh_token = st.secrets["github"]["token"]
        gh_repo = st.secrets["github"]["repo"]
        return gh_token, gh_repo
    except Exception:
        return None, None

def load_memos():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return get_default_memos()

def save_memos(memos):
    # 1. 瞬间写入本地文件（保证零延迟响应，绝不卡顿）
    content_str = json.dumps(memos, ensure_ascii=False, indent=4)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(content_str)
    
    # 2. 后台静默尝试推送到 GitHub
    token, repo = get_github_config()
    if not token or not repo:
        return
    
    try:
        url = f"https://api.github.com/repos/{repo}/contents/{DATA_FILE}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        
        res = requests.get(url, headers=headers, timeout=3)
        sha = res.json().get("sha", "") if res.status_code == 200 else ""
        
        content_encoded = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
        data = {
            "message": f"Sync memo at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": content_encoded,
            "sha": sha
        }
        requests.put(url, headers=headers, json=data, timeout=3)
    except Exception:
        pass # 网络不好时静默跳过，保证本地丝滑

def get_default_memos():
    return [
        {
            "id": 1,
            "client_name": "王姐",
            "phone": "13812345678",
            "address": "金地花园 2栋 501",
            "service": "上门通下水道",
            "fee": 150.0,
            "date": str(datetime.now().date()),
            "is_urgent": True,
            "status": "进行中",
            "memo_desc": "顾客要求下午3点前到",
            "delete_reason": ""
        }
    ]

# ---------------- 2. 安全密码登录验证 ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = "staff"

if not st.session_state.logged_in:
    st.title("🔐 小店智能备忘录系统登录")
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("用户名 (staff 或 boss)")
            password = st.text_input("密码", type="password")
            submit = st.form_submit_button("🚀 登录系统")
            if submit:
                try:
                    correct_pwd = st.secrets["passwords"][username]
                except Exception:
                    default_passwords = {"staff": "123", "boss": "123"}
                    correct_pwd = default_passwords.get(username)

                if correct_pwd and password == correct_pwd:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "boss" if username == "boss" else "staff"
                    st.success("登录成功！正在进入...")
                    st.rerun()
                else:
                    st.error("用户名不存在或密码错误！(默认测试密码可输入 123)")
    st.stop()

# ---------------- 3. 主体系统界面 ----------------
st.title("📋 小店智能备忘录与协同系统")
current_role = st.session_state.user_role

st.sidebar.markdown(f"**当前身份**：`{current_role.upper()}`")
if current_role == "boss":
    st.sidebar.info("👑 老板娘模式：最高审批与管理权限")
else:
    st.sidebar.info("✍️ 员工模式：登记、申请完成与申请删除")

if st.sidebar.button("🚪 退出登录"):
    st.session_state.logged_in = False
    st.rerun()

# ---------------- 4. 员工端 ----------------
if current_role == "staff":
    st.subheader("✍️ 员工端：快速登记客户预约与备忘")
    
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("客户姓名 / 称呼 *", key="input_client")
        phone = st.text_input("联系电话", key="input_phone")
        address = st.text_input("上门服务地址", key="input_address")
    with col2:
        service = st.text_input("服务项目 *", key="input_service")
        fee = st.number_input("预计费用 (￥)", min_value=0.0, value=0.0, step=10.0, key="input_fee")
        date = st.date_input("预约日期", value=datetime.now(), key="input_date")
    
    desc = st.text_area("详细备注", key="input_desc")
    is_urgent = st.checkbox("🔥 标记为【加急件 / 优先处理】", value=False, key="input_urgent")
    
    submitted = st.button("✅ 提交并保存备忘", type="primary")
    if submitted:
        if not client_name or not service:
            st.error("⚠️ 录入失败：请完整填写【客户姓名】和【服务项目】！（输入内容已完整保留）")
        else:
            memos = load_memos()
            new_item = {
                "id": int(datetime.now().timestamp()),
                "client_name": client_name,
                "phone": phone,
                "address": address,
                "service": service,
                "fee": fee,
                "date": str(date),
                "is_urgent": is_urgent,
                "status": "进行中",
                "memo_desc": desc,
                "delete_reason": ""
            }
            memos.insert(0, new_item)
            save_memos(memos)
            st.success("🎉 登记成功！")
            st.rerun()

    st.markdown("---")
    st.subheader("📝 近期备忘与进度申请中心")
    
    memos = load_memos()
    
    for m in memos:
        if m["status"] == "已完成":
            status_badge = "✨ 已完成"
        elif m["status"] == "待审核":
            status_badge = "⏳ 待老板娘审核(完成)"
        elif m["status"] == "待删除审核":
            status_badge = "🗑️ 待老板娘审核(删除)"
        else:
            status_badge = "🏃 进行中"

        urgent_badge = "🔥 **[加急]**" if m["is_urgent"] else ""
        
        with st.container():
            st.markdown(f"""
            ### {urgent_badge} {m['client_name']} —— {m['service']} (￥{m['fee']})
            - **📞 电话**：`{m['phone'] or '未填'}` | **📍 地址**：{m['address'] or '未填'} | **📅 日期**：{m['date']}
            - **📌 当前状态**：`{status_badge}` | **📝 备注**：{m['memo_desc'] or '无'}
            """)
            
            if m["status"] == "进行中":
                if st.button("👉 申请完成（提交老板娘审核）", key=f"staff_apply_{m['id']}"):
                    m["status"] = "待审核"
                    save_memos(memos)
                    st.success("已提交完成申请！")
                    st.rerun()
                
                with st.expander("🛠️ 登记错误？申请删除此单"):
                    del_reason_input = st.text_input("请填写申请删除的理由 *", key=f"reason_input_{m['id']}", placeholder="例如：客户取消预约...")
                    if st.button("📤 提交删除申请给老板娘", key=f"staff_del_req_{m['id']}"):
                        if not del_reason_input.strip():
                            st.warning("请先填写删除理由！")
                        else:
                            m["status"] = "待删除审核"
                            m["delete_reason"] = del_reason_input
                            save_memos(memos)
                            st.success("删除申请已提交！")
                            st.rerun()

            elif m["status"] == "待审核":
                st.info("📌 已提交完成申请，等待老板娘审批确认中...")
            elif m["status"] == "待删除审核":
                st.warning(f"⚠️ 已提交删除申请，删除理由：【{m.get('delete_reason', '无')}】等待老板娘审批...")
            elif m["status"] == "已完成":
                st.success("✨ 此单已由老板娘审核通过并归档。")

            st.markdown("---")

# ---------------- 5. 老板娘端 ----------------
else:
    st.subheader("👑 老板娘核心看板与审批中心")
    
    memos = load_memos()
    
    total_count = len(memos)
    urgent_count = sum(1 for m in memos if m["is_urgent"] and m["status"] not in ["已完成", "待删除审核"])
    pending_approval_count = sum(1 for m in memos if m["status"] in ["待审核", "待删除审核"])
    total_revenue = sum(m["fee"] for m in memos if m["status"] not in ["已完成", "待删除审核"])
    
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("总单数", f"{total_count} 单")
    col_b.metric("🔥 紧急加急", f"{urgent_count} 单")
    col_c.metric("⏳ 待审批事项", f"{pending_approval_count} 单")
    col_d.metric("进行中预计营收", f"￥{total_revenue:.2f}")
    
    st.markdown("---")
    
    filter_option = st.radio("看板筛选", ["全部显示", "⏳ 待审批的单子", "🔥 仅看加急件", "已完成单子"], horizontal=True)
    
    filtered_memos = memos
    if filter_option == "⏳ 待审批的单子":
        filtered_memos = [m for m in memos if m["status"] in ["待审核", "待删除审核"]]
    elif filter_option == "🔥 仅看加急件":
        filtered_memos = [m for m in memos if m["is_urgent"]]
    elif filter_option == "已完成单子":
        filtered_memos = [m for m in memos if m["status"] == "已完成"]
    
    st.markdown(f"**当前显示记录数**：{len(filtered_memos)} 条")
    st.markdown("---")
    
    if not filtered_memos:
        st.info("当前筛选目录下没有单子。")
    else:
        for m in filtered_memos:
            if m["status"] == "已完成":
                status_badge = "✨ 已完成"
            elif m["status"] == "待审核":
                status_badge = "⏳ 待老板娘审核(完成)"
            elif m["status"] == "待删除审核":
                status_badge = "🗑️ ⚠️ 员工申请删除此单"
            else:
                status_badge = "🏃 进行中"

            urgent_str = "🔥 **[加急件]**" if m["is_urgent"] else ""
            
            with st.container():
                st.markdown(f"""
                ### {urgent_str} {m['client_name']} —— {m['service']} (￥{m['fee']})
                - **📞 电话**：`{m['phone'] or '未填'}` | **📍 地址**：{m['address'] or '未填'} | **📅 日期**：{m['date']}
                - **📌 状态**：`{status_badge}`
                - **📝 备注**：{m['memo_desc'] or '无'}
                """)
                
                if m["status"] == "待删除审核":
                    st.error(f"🚨 **员工申请删除理由**：{m.get('delete_reason', '无')} —— 请核实后决定是否批准！")

                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
                
                if m["status"] == "待审核":
                    with col_btn1:
                        if st.button("✅ 批准完成", key=f"boss_approve_{m['id']}"):
                            m["status"] = "已完成"
                            save_memos(memos)
                            st.success("已批准该单完成！")
                            st.rerun()
                    with col_btn2:
                        if st.button("❌ 驳回申请", key=f"boss_reject_{m['id']}"):
                            m["status"] = "进行中"
                            save_memos(memos)
                            st.warning("已驳回，退回进行中。")
                            st.rerun()
                            
                elif m["status"] == "待删除审核":
                    with col_btn1:
                        if st.button("✅ 批准删除（彻底移除）", key=f"boss_approve_del_{m['id']}"):
                            memos = [item for item in memos if item["id"] != m["id"]]
                            save_memos(memos)
                            st.warning("已彻底清除该单！")
                            st.rerun()
                    with col_btn2:
                        if st.button("❌ 驳回删除申请", key=f"boss_reject_del_{m['id']}"):
                            m["status"] = "进行中"
                            m["delete_reason"] = ""
                            save_memos(memos)
                            st.info("已驳回删除，恢复为进行中状态。")
                            st.rerun()
                            
                elif m["status"] == "已完成":
                    with col_btn1:
                        if st.button("🔄 重新设为进行中", key=f"boss_reopen_{m['id']}"):
                            m["status"] = "进行中"
                            save_memos(memos)
                            st.rerun()
                
                if m["status"] != "待删除审核":
                    with col_btn2:
                        if st.button("🗑️ 直接删除", key=f"boss_del_{m['id']}"):
                            memos = [item for item in memos if item["id"] != m["id"]]
                            save_memos(memos)
                            st.warning("已直接删除该单。")
                            st.rerun()

                st.markdown("---")
