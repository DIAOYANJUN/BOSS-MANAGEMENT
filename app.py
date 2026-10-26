import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# ---------------- 0. 页面配置与持久化存储设置 ----------------
st.set_page_config(
    page_title="小店智能备忘录与协同系统",
    page_icon="📋",
    layout="wide"
)

DATA_FILE = "memos.json"

# 加载共享数据
def load_memos():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
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
            "delete_reason": "" # 用于存放删除申请的理由
        }
    ]

# 保存共享数据
def save_memos(memos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(memos, f, ensure_ascii=False, indent=4)

if "memos" not in st.session_state:
    st.session_state.memos = load_memos()

# ---------------- 1. 安全密码登录验证 ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = "staff"

if not st.session_state.logged_in:
    st.title("🔐 小店备忘录系统登录")
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

# ---------------- 2. 主体系统界面（角色权限严格隔离） ----------------
st.title("📋 小店智能备忘录与协同系统")
current_role = st.session_state.user_role

st.sidebar.markdown(f"**当前身份**：`{current_role.upper()}`")
if current_role == "boss":
    st.sidebar.info("👑 老板娘模式：拥有最高审批与管理权限")
else:
    st.sidebar.info("✍️ 员工模式：可登记新单、申请完成与申请删除")

if st.sidebar.button("🚪 退出登录"):
    st.session_state.logged_in = False
    st.rerun()

# ---------------- 3. 员工专属端（可录入、可申请完成、可带理由申请删除） ----------------
if current_role == "staff":
    st.subheader("✍️ 员工端：快速登记客户预约与备忘")
    
    # 防误删普通输入框
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
            st.session_state.memos.insert(0, new_item)
            save_memos(st.session_state.memos)
            st.success("🎉 登记成功！已同步至小店共享账本。")

    st.markdown("---")
    st.subheader("📝 近期备忘与进度申请中心")
    
    st.session_state.memos = load_memos()
    
    for m in st.session_state.memos:
        # 状态文案
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
            
            # 员工操作逻辑
            if m["status"] == "进行中":
                # 1. 申请完成按钮
                if st.button("👉 申请完成（提交老板娘审核）", key=f"staff_apply_{m['id']}"):
                    m["status"] = "待审核"
                    save_memos(st.session_state.memos)
                    st.success("已提交完成申请！")
                    st.rerun()
                
                # 2. 带有折叠/输入框的申请删除逻辑
                with st.expander("🛠️ 登记错误？申请删除此单"):
                    del_reason_input = st.text_input("请填写申请删除的理由 *", key=f"reason_input_{m['id']}", placeholder="例如：客户取消预约，或者录错电话...")
                    if st.button("📤 提交删除申请给老板娘", key=f"staff_del_req_{m['id']}"):
                        if not del_reason_input.strip():
                            st.warning("请先填写删除理由！")
                        else:
                            m["status"] = "待删除审核"
                            m["delete_reason"] = del_reason_input
                            save_memos(st.session_state.memos)
                            st.success("删除申请已提交，等待老板娘批准！")
                            st.rerun()

            elif m["status"] == "待审核":
                st.info("📌 已提交完成申请，等待老板娘审批确认中...")
            elif m["status"] == "待删除审核":
                st.warning(f"⚠️ 已提交删除申请，删除理由：【{m.get('delete_reason', '无')}】等待老板娘审批...")
            elif m["status"] == "已完成":
                st.success("✨ 此单已由老板娘审核通过并归档。")

            st.markdown("---")

# ---------------- 4. 老板娘专属核心看板（审批与管理中心） ----------------
else:
    st.subheader("👑 老板娘核心看板与审批中心")
    
    st.session_state.memos = load_memos()
    memos = st.session_state.memos
    
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
                
                # 如果是员工申请删除的单子，把删除理由重点标红显示
                if m["status"] == "待删除审核":
                    st.error(f"🚨 **员工申请删除理由**：{m.get('delete_reason', '无')} —— 请核实后决定是否批准删除！")

                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
                
                # 老板娘审批操作
                if m["status"] == "待审核":
                    with col_btn1:
                        if st.button("✅ 批准完成", key=f"boss_approve_{m['id']}"):
                            m["status"] = "已完成"
                            save_memos(st.session_state.memos)
                            st.success("已批准该单完成！")
                            st.rerun()
                    with col_btn2:
                        if st.button("❌ 驳回申请", key=f"boss_reject_{m['id']}"):
                            m["status"] = "进行中"
                            save_memos(st.session_state.memos)
                            st.warning("已驳回，退回进行中。")
                            st.rerun()
                            
                elif m["status"] == "待删除审核":
                    with col_btn1:
                        if st.button("✅ 批准删除（彻底移除）", key=f"boss_approve_del_{m['id']}"):
                            st.session_state.memos = [item for item in st.session_state.memos if item["id"] != m["id"]]
                            save_memos(st.session_state.memos)
                            st.warning("已批准删除并彻底清除该单！")
                            st.rerun()
                    with col_btn2:
                        if st.button("❌ 驳回删除申请", key=f"boss_reject_del_{m['id']}"):
                            m["status"] = "进行中"
                            m["delete_reason"] = ""
                            save_memos(st.session_state.memos)
                            st.info("已驳回删除申请，恢复为进行中状态。")
                            st.rerun()
                            
                elif m["status"] == "已完成":
                    with col_btn1:
                        if st.button("🔄 重新设为进行中", key=f"boss_reopen_{m['id']}"):
                            m["status"] = "进行中"
                            save_memos(st.session_state.memos)
                            st.rerun()
                
                # 老板娘随时可以直接删除普通单子
                if m["status"] != "待删除审核":
                    with col_btn2:
                        if st.button("🗑️ 直接删除", key=f"boss_del_{m['id']}"):
                            st.session_state.memos = [item for item in st.session_state.memos if item["id"] != m["id"]]
                            save_memos(st.session_state.memos)
                            st.warning("已直接删除该单。")
                            st.rerun()

                st.markdown("---")