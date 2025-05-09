import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
from io import BytesIO
from fpdf import FPDF

# -------------------- 사용자 설정 --------------------
if "users" not in st.session_state:
    st.session_state.users = {
        "admin": hashlib.sha256("admin123".encode()).hexdigest(),
        "sales1": hashlib.sha256("pass1".encode()).hexdigest(),
    }

if "projects" not in st.session_state:
    st.session_state.projects = []

if "visits" not in st.session_state:
    st.session_state.visits = []

# -------------------- 로그인 기능 --------------------
def login():
    st.sidebar.title("🔐 로그인")
    username = st.sidebar.text_input("사용자명")
    password = st.sidebar.text_input("비밀번호", type="password")
    login_btn = st.sidebar.button("로그인")

    if login_btn:
        if username in st.session_state.users and hashlib.sha256(password.encode()).hexdigest() == st.session_state.users[username]:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.rerun()
        else:
            st.sidebar.error("❌ 로그인 실패. 사용자명 또는 비밀번호 확인")

    if st.sidebar.checkbox("📌 관리자 계정으로 사용자 관리"):
        admin_id = st.sidebar.text_input("🔑 관리자 ID")
        admin_pw = st.sidebar.text_input("🔑 관리자 비밀번호", type="password")
        if (admin_id == "admin" and hashlib.sha256(admin_pw.encode()).hexdigest() == st.session_state.users["admin"]):
            st.sidebar.markdown("---")
            new_user = st.sidebar.text_input("👤 새 사용자명")
            new_pw = st.sidebar.text_input("🔐 새 비밀번호", type="password")
            if st.sidebar.button("➕ 사용자 생성"):
                if new_user and new_pw:
                    st.session_state.users[new_user] = hashlib.sha256(new_pw.encode()).hexdigest()
                    st.sidebar.success(f"✅ 사용자 {new_user} 생성 완료")
                else:
                    st.sidebar.warning("입력값을 모두 입력해주세요")

            st.sidebar.markdown("---")
            reset_user = st.sidebar.text_input("🔄 초기화할 사용자명")
            reset_pw = st.sidebar.text_input("🆕 새 비밀번호", type="password")
            if st.sidebar.button("🔁 비밀번호 초기화"):
                if reset_user in st.session_state.users:
                    st.session_state.users[reset_user] = hashlib.sha256(reset_pw.encode()).hexdigest()
                    st.sidebar.success(f"🔐 {reset_user}의 비밀번호가 초기화되었습니다")
                else:
                    st.sidebar.error("사용자를 찾을 수 없습니다")

# -------------------- PDF 생성 함수 --------------------
def create_pdf(data, project):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"프로젝트: {project} 관리 기록", ln=True, align='L')
    pdf.ln(5)

    for item in data:
        pdf.multi_cell(0, 10, txt=f"[{item['date']}] {item['user']} / {item['method']} / 중요도: {item['importance']}", border=0)
        pdf.multi_cell(0, 10, txt=f"연락자: {item.get('contact_person', '')}", border=0)
        pdf.multi_cell(0, 10, txt=f"내용: {item['note']}", border=0)
        pdf.multi_cell(0, 10, txt=f"다음 액션: {item.get('next_action', '')}", border=0)
        pdf.ln(5)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

# -------------------- CRM 화면 --------------------
def show_crm():
    st.title("📁 프로젝트 CRM 대시보드")

    project = st.selectbox("📌 프로젝트 선택", st.session_state.projects + ["신규 입력"])

    if project == "신규 입력":
        new_proj = st.text_input("새 프로젝트명 입력")
        if st.button("등록"):
            if new_proj and new_proj not in st.session_state.projects:
                st.session_state.projects.append(new_proj)
                st.success("✅ 신규 프로젝트가 추가되었습니다.")
                st.rerun()
            else:
                st.warning("이미 존재하거나 입력값이 없습니다.")
        return

    st.markdown("---")
    st.subheader("📞 관리 기록")

    with st.form("visit_form"):
        visit_date = st.date_input("날짜", value=datetime.today())
        method = st.selectbox("접촉 방식", ["방문", "전화", "이메일", "기타"])
        contact_person = st.text_input("연락자")
        importance = st.selectbox("중요도", ["긴급", "일반", "낮음"])
        next_action = st.text_area("다음 액션")
        note = st.text_area("상세 내용")
        submitted = st.form_submit_button("기록 추가")
        if submitted:
            st.session_state.visits.append({
                "project": project,
                "user": st.session_state.user,
                "date": str(visit_date),
                "method": method,
                "contact_person": contact_person,
                "importance": importance,
                "next_action": next_action,
                "note": note
            })
            st.success("✅ 관리 기록이 추가되었습니다")

    st.markdown("### 🔎 관리 기록 필터")
    colf1, colf2, colf3 = st.columns(3)
    filter_date = colf1.date_input("날짜 기준", value=None)
    filter_importance = colf2.selectbox("중요도 필터", ["전체"] + ["긴급", "일반", "낮음"])
    filter_person = colf3.text_input("연락자명 필터")

    filtered_data = []
    for v in st.session_state.visits:
        if v["project"] == project:
            if filter_date and v['date'] != str(filter_date):
                continue
            if filter_importance != "전체" and v['importance'] != filter_importance:
                continue
            if filter_person and filter_person not in v['contact_person']:
                continue
            filtered_data.append(v)

    colx1, colx2 = st.columns(2)
    with colx1:
        if st.button("📤 Excel로 내보내기"):
            df = pd.DataFrame(filtered_data)
            st.download_button(
                label="Excel 다운로드",
                data=df.to_excel(index=False, engine='openpyxl'),
                file_name=f"{project}_관리기록.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    with colx2:
        if st.button("🧾 PDF로 내보내기"):
            pdf_data = create_pdf(filtered_data, project)
            st.download_button(
                label="PDF 다운로드",
                data=pdf_data,
                file_name=f"{project}_관리기록.pdf",
                mime="application/pdf"
            )

    st.markdown("### 📚 관리 기록 타임라인")
    indices_to_remove = []
    for i, v in enumerate(reversed(st.session_state.visits)):
        actual_index = len(st.session_state.visits) - 1 - i
        if v["project"] == project:
            if filter_date and v['date'] != str(filter_date):
                continue
            if filter_importance != "전체" and v['importance'] != filter_importance:
                continue
            if filter_person and filter_person not in v['contact_person']:
                continue

            with st.expander(f"[{v['date']}] {v['user']} ({v['method']})"):
                edited_note = st.text_area("내용 수정", value=v['note'], key=f"edit_{actual_index}")
                edited_action = st.text_area("다음 액션 수정", value=v.get("next_action", ""), key=f"action_{actual_index}")
                cols = st.columns([1, 1])
                if cols[0].button("💾 수정", key=f"save_{actual_index}"):
                    st.session_state.visits[actual_index]['note'] = edited_note
                    st.session_state.visits[actual_index]['next_action'] = edited_action
                    st.success("✅ 내용이 수정되었습니다")
                if cols[1].button("🗑️ 삭제", key=f"delete_{actual_index}"):
                    indices_to_remove.append(actual_index)

    for index in sorted(indices_to_remove, reverse=True):
        del st.session_state.visits[index]

# -------------------- 메인 --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    show_crm()