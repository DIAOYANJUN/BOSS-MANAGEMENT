import streamlit as st
import pandas as pd
import json
import base64
import requests
import os
from datetime import datetime
from streamlit_cookies_controller import CookieController

# ---------------- 0. 页面配置与 Cookie 控制器初始化 ----------------
st.set_page_config(
    page_title="小店智能备忘录与协同系统",
    page_icon="📋",
    layout="wide"
)

# 初始化安全的 Cookie 控制器
cookie_controller = CookieController()

DATA_FILE = "memos.json"

# ---------------- 1. 核心数据读写与同步 ----------------
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
    content_str = json.dumps(memos, ensure_ascii=False, indent=4)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(content_str)
    
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
        pass

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

# ---------------- 2. 安全的 Cookie 登录态维持 ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = "staff"

# 从浏览器的加密 Cookie 中读取登录状态
cookie_logged = cookie_controller.get("boss_memo_logged")
cookie_role = cookie_controller.get("boss_memo_role")

if cookie_logged == "true":
    st.session_state.logged_in = True
    st.session_state.user_role = cookie_role if cookie_role else "staff"

if not st.session_state.logged_in:
    st.title("🔐 小店智能备忘录系统登录")
    st.markdown("---")
    
    col_img, col_login = st.columns([1, 1], gap="large")
    
    with col_img:
        st.markdown("### 🐾 欢迎来到小店！")
        if os.path.exists("bubu.jpeg"):
            st.image("bubu.jpeg", use_container_width=True, caption="bubu")
        if os.path.exists("yier.jpeg"):
            st.image("yier.jpeg", use_container_width=True, caption="yier")
            
    with col_login:
        st.markdown("### 🚀 请输入账号密码")
        with st.form("login_form"):
            username = st.text_input("用户名 (staff 或 boss)")
            password = st.text_input("密码", type="password")
            submit = st.form_submit_button("🚀 登录系统", use_container_width=True)
            if submit:
                try:
                    correct_pwd = st.secrets["passwords"][username]
                except Exception:
                    default_passwords = {"staff": "123", "boss": "123"}
                    correct_pwd = default_passwords.get(username)

                if correct_pwd and password == correct_pwd:
                    role_to_set = "boss" if username == "boss" else "staff"
                    # 将登录状态存入加密 Cookie（有效期 7 天）
                    cookie_controller.set("boss_memo_logged", "true", max_age=60*60*24*7)
                    cookie_controller.set("boss_memo_role", role_to_set, max_age=60*60*24*7)
                    
                    st.session_state.logged_in = True
                    st.session_state.user_role = role_to_set
                    st.success("登录成功！正在进入...")
                    st.rerun()
                else:
                    st.error("用户名不存在或密码错误！(默认测试密码可输入 123)")
    st.stop()

# ---------------- 3. 主体系统界面与侧边栏 ----------------
st.title("📋 小店智能备忘录与协同系统")
current_role = st.session_state.user_role

# 动态设备时钟
clock_html = """
<div style="font-family: sans-serif; font-size: 13px; font-weight: bold; color: #31333F; background: #f0f2f6; padding: 8px; border-radius: 6px; text-align: center;">
    🕒 <span id="clock">获取时间中...</span>
</div>
<script>
function updateClock() {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, '0');
    const d = String(now.getDate()).padStart(2, '0');
    const h = String(now.getHours()).padStart(2, '0');
    const min = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    const el = document.getElementById('clock');
    if (el) el.innerText = `${y}-${m}-${d} ${h}:${min}:${s}`;
}
setInterval(updateClock, 1000);
updateClock();
</script>
"""
with st.sidebar:
    st.components.v1.html(clock_html, height=45)
    st.markdown(f"👤 **当前身份**：`{current_role.upper()}`")

    if current_role == "boss":
        st.info("👑 老板娘模式：全面看板、审批与管理权限")
    else:
        st.info("✍️ 员工模式：登记预约与进度协同")

    if os.path.exists("lulu.jpeg"):
        st.image("lulu.jpeg", use_container_width=True)

    st.markdown("---")

    if st.button("🔄 刷新并核对状态", type="primary", use_container_width=True):
        st.toast("已成功重新加载最新状态！", icon="✅")
        st.rerun()

    if st.button("🚪 退出登录", use_container_width=True):
        # 清除浏览器的加密 Cookie
        cookie_controller.remove("boss_memo_logged")
        cookie_controller.remove("boss_memo_role")
        st.session_state.logged_in = False
        st.rerun()

# ---------------- 公共函数：渲染可清空的录入表单 ----------------
def render_memo_input_form(form_key_suffix=""):
    st.subheader("✍️ 快速登记客户预约与报价")
    
    with st.form(f"memo_input_form_{form_key_suffix}", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            client_name = st.text_input("客户姓名 / 称呼 *")
            phone = st.text_input("联系电话")
            address = st.text_input("上门服务地址")
        with col2:
            service = st.text_input("服务项目 *")
            fee = st.number_input("服务报价 (￥)", min_value=0.0, value=0.0, step=10.0)
            date = st.date_input("预约日期", value=datetime.now())
        
        desc = st.text_area("详细备注")
        is_urgent = st.checkbox("🔥 标记为【加急件 / 优先处理】", value=False)
        
        submitted = st.form_submit_button("✅ 提交并保存备忘", use_container_width=True)
        if submitted:
            if not client_name or not service:
                st.error("⚠️ 录入失败：请完整填写【客户姓名】和【服务项目】！")
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
                st.session_state["success_msg"] = f"🎉 成功保存【{client_name}】的预约单！输入已清空。"
                st.rerun()

    if "success_msg" in st.session_state and st.session_state["success_msg"]:
        st.success(st.session_state["success_msg"])
        del st.session_state["success_msg"]

# ---------------- 排序助手函数 ----------------
def sort_memos(memos, sort_option):
    if sort_option == "金额：从高到低 ⬇️":
        return sorted(memos, key=lambda x: x["fee"], reverse=True)
    elif sort_option == "金额：从低到高 ⬆️":
        return sorted(memos, key=lambda x: x["fee"], reverse=False)
    elif sort_option == "日期：由早到迟（最早的在前） ⏰":
        return sorted(memos, key=lambda x: x["date"], reverse=False)
    elif sort_option == "日期：由迟到早（最晚的在前） 📅":
        return sorted(memos, key=lambda x: x["date"], reverse=True)
    return memos

# ---------------- 4. 顶部快捷操作栏（增加备忘录 & 手机号搜索） ----------------
st.markdown("---")
top_col1, top_col2, top_col3 = st.columns([1, 1, 2])

with top_col1:
    show_add_form = st.toggle("➕ 增加备忘录", value=False)
with top_col2:
    show_search = st.toggle("🔍 搜索备忘录", value=False)

if show_add_form:
    render_memo_input_form("top_add_form")
    st.markdown("---")

search_phone_query = ""
if show_search:
    with st.container():
        st.info("💡 提示：请输入客户的完整手机号或部分手机号数字进行实时精准检索。")
        search_phone_query = st.text_input("📞 输入手机号搜索", placeholder="例如：138 或 1234...")
    st.markdown("---")

# ---------------- 5. 员工端 ----------------
if current_role == "staff":
    col_title, col_sort = st.columns([2, 2])
    with col_title:
        st.subheader("📝 近期备忘与进度申请中心")
    with col_sort:
        sort_option = st.selectbox(
            "🔀 排序方式",
            ["默认排序", "日期：由早到迟（最早的在前） ⏰", "日期：由迟到早（最晚的在前） 📅", "金额：从高到低 ⬇️", "金额：从低到高 ⬆️"],
            key="staff_sort"
        )
    
    memos = load_memos()
    
    if show_search and search_phone_query.strip():
        memos = [m for m in memos if search_phone_query.strip() in m.get("phone", "")]
    
    memos = sort_memos(memos, sort_option)
    
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
            ### {urgent_badge} {m['client_name']} —— {m['service']} (报价: ￥{m['fee']})
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
                    confirm_del = st.checkbox("⚠️ 我确认要向老板娘提交该单的删除申请", key=f"confirm_del_staff_{m['id']}")
                    if st.button("📤 提交删除申请给老板娘", key=f"staff_del_req_{m['id']}"):
                        if not del_reason_input.strip():
                            st.warning("请先填写删除理由！")
                        elif not confirm_del:
                            st.warning("⚠️ 请先勾选上方的“确认提交删除申请”复选框！")
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

# ---------------- 6. 老板娘端 ----------------
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
    col_d.metric("💰 进行中总营收", f"￥{total_revenue:.2f}")
    
    st.markdown("---")
    
    col_filter, col_sort = st.columns([3, 2])
    with col_filter:
        filter_option = st.radio("看板筛选", ["全部显示", "⏳ 待审批的单子", "🔥 仅看加急件", "已完成单子"], horizontal=True)
    with col_sort:
        sort_option = st.selectbox(
            "🔀 列表排序方式",
            ["默认排序", "日期：由早到迟（最早的在前） ⏰", "日期：由迟到早（最晚的在前） 📅", "金额：从高到低 ⬇️", "金额：从低到高 ⬆️"],
            key="boss_sort"
        )
    
    filtered_memos = memos
    if filter_option == "⏳ 待审批的单子":
        filtered_memos = [m for m in memos if m["status"] in ["待审核", "待删除审核"]]
    elif filter_option == "🔥 仅看加急件":
        filtered_memos = [m for m in memos if m["is_urgent"]]
    elif filter_option == "已完成单子":
        filtered_memos = [m for m in memos if m["status"] == "已完成"]
    
    if show_search and search_phone_query.strip():
        filtered_memos = [m for m in filtered_memos if search_phone_query.strip() in m.get("phone", "")]
    
    filtered_memos = sort_memos(filtered_memos, sort_option)
    
    st.markdown(f"**当前显示记录数**：{len(filtered_memos)} 条")
    st.markdown("---")
    
    if not filtered_memos:
        st.info("当前筛选或搜索条件下没有找到单子。")
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
                        with st.popover("🗑️ 删除此单"):
                            st.error("⚠️ 警告：此操作将永久抹除该单记录！")
                            confirm_boss_del = st.checkbox("确认要彻底删除吗？", key=f"chk_boss_del_{m['id']}")
                            if st.button("确认无误，执行删除", key=f"btn_boss_del_exec_{m['id']}", type="primary"):
                                if confirm_boss_del:
                                    memos = [item for item in memos if item["id"] != m["id"]]
                                    save_memos(memos)
                                    st.warning("已直接删除该单。")
                                    st.rerun()
                                else:
                                    st.warning("请先勾选上方的“确认要彻底删除吗”！")

                st.markdown("---")
