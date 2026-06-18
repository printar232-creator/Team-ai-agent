import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIG & INITIALIZATION ---
st.set_page_config(page_title="AI Team Enterprise System", page_icon="🤖", layout="wide")

# ดึง API Key จาก Streamlit Secrets (ปลอดภัยที่สุดเมื่อรันบน Cloud/GitHub)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("❌ ไม่พบ GEMINI_API_KEY ใน Streamlit Secrets! กรุณาตั้งค่าก่อนใช้งาน")
    st.stop()

# --- 2. DEFINING THE AGENTS (PROMPTS) ---
# นิยามบทบาทของแต่ละทีมเพื่อให้ Manager เรียกใช้
TEAMS_INFO = {
    "Production": "ดูแลเรื่องกระบวนการผลิต การวางแผนโรงงาน สินค้าคงคลัง และ Supply Chain",
    "Lab": "ดูแลเรื่องการวิจัยและพัฒนา (R&D) การทดลอง สูตรเคมี/ผลิตภัณฑ์ และการควบคุมคุณภาพ (QC)",
    "HR": "ดูแลเรื่องทรัพยากรบุคคล การจัดจ้าง การประเมินผล สวัสดิการ และการอบรมพนักงาน",
    "Account": "ดูแลเรื่องการเงิน บัญชี งบประมาณ รายรับ-รายจ่าย และความคุ้มทุน"
}

# --- 3. HELPER FUNCTIONS ---
def ask_gemini(system_instruction, prompt):
    """ฟังก์ชันส่งคำสั่งหา Gemini ตามบทบาทที่กำหนด"""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}"

def manager_delegate(user_task):
    """สมองส่วนกลาง (Manager) วิเคราะห์ว่างานนี้ต้องให้ทีมไหนทำบ้าง"""
    manager_instruction = (
        "คุณคือ CEO และ Manager AI อัจฉริยะ ทำหน้าที่รับบรีฟงานจากผู้ใช้ "
        "แล้ววิเคราะห์ว่างานนี้จำเป็นต้องส่งต่อให้ทีมใดใน 4 ทีมนี้บ้าง: Production, Lab, HR, Account "
        "คุณต้องตอบกลับเป็นรูปแบบ JSON Array เท่านั้น เช่น ['Production', 'Lab'] "
        "วิเคราะห์ให้ดีว่างานเกี่ยวพันกับทีมไหนบ้าง (สามารถตอบได้มากกว่า 1 ทีม หรือตอบทั้งหมดถ้าเกี่ยวกันทั้งหมด) "
        "ห้ามอธิบายข้อความอื่นนอกเหนือจาก JSON format เด็ดขาด"
    )
    
    prompt = f"งานที่ได้รับ: '{user_task}' \n\nทีมที่มีอยู่: {json.dumps(TEAMS_INFO, ensure_ascii=False)}"
    response_text = ask_gemini(manager_instruction, prompt)
    
    # Clean response clean เผื่อ Gemini ใส่ markdown block ```json ... ``` มา
    clean_text = response_text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean_text)
    except:
        # Fallback กรณีแปลง JSON พลาด ให้ส่งให้ทุกทีมช่วยกันดู
        return list(TEAMS_INFO.keys())

# --- 4. STREAMLIT UI ---
st.title("🤖 Enterprise AI Team Network")
st.subheader("ระบบบริหารงานอัตโนมัติด้วยสมองส่วนกลาง Gemini")
st.write("---")

# ส่วนรับ Input จากผู้ใช้
user_input = st.text_area(
    "📥 ใส่โจทย์หรือคำสั่งงานที่ต้องการให้ทีม AI ช่วยกันคิด:",
    placeholder="เช่น 'เราต้องการผลิตเครื่องดื่มชูกำลังรสชาติใหม่เพื่อเจาะตลาดวัยรุ่น ต้องเตรียมตัวอย่างไรบ้าง'"
)

if st.button("🚀 สั่งการทีม AI", type="primary"):
    if user_input.strip() == "":
        st.warning("กรุณากรอกคำสั่งงานก่อนครับ")
    else:
        # ขั้นตอนที่ 1: Manager วิเคราะห์แยกงาน
        with st.spinner("🧠 สมองส่วนกลาง (Gemini Manager) กำลังวิเคราะห์และแจกจ่ายงาน..."):
            assigned_teams = manager_delegate(user_input)
        
        st.success(f"📋 **Manager สั่งการ:** มอบหมายงานนี้ให้แก่ทีม: {', '.join(assigned_teams)}")
        st.write("---")
        
        # ขั้นตอนที่ 2: ให้ทีมที่ได้รับมอบหมายทำงานขนานกัน
        # สร้างคอลัมน์ใน Streamlit ตามจำนวนทีมที่ถูกเลือก
        cols = st.columns(len(assigned_teams))
        
        for idx, team_name in enumerate(assigned_teams):
            with cols[idx]:
                st.markdown(f"### 🏢 ทีม: {team_name}")
                st.caption(TEAMS_INFO[team_name])
                
                with st.spinner(f"⏳ ทีม {team_name} กำลังประมวลผล..."):
                    # สร้าง Instruction เฉพาะของทีมนั้นๆ
                    team_instruction = (
                        f"คุณคือหัวหน้าทีม {team_name} ที่เชี่ยวชาญระดับโลก หน้าที่ของคุณคือ: {TEAMS_INFO[team_name]} "
                        f"จงวิเคราะห์ข้อสรุป แนวทางปฏิบัติ หรือวิธีแก้ปัญหาในมุมมองของทีมคุณ "
                        f"จากโจทย์ที่ได้รับ โดยเน้นเนื้อหาที่จับต้องได้ นำไปใช้จริงได้"
                    )
                    
                    # ให้ Agent ประจำทีมคิดคำตอบ
                    team_response = ask_gemini(team_instruction, user_input)
                    
                    # แสดงผลแยกตามกล่อง/ทีม
                    st.info(team_response)

        # ขั้นตอนที่ 3: สรุปรวม (Optional)
        st.write("---")
        with st.spinner("📝 Manager กำลังรวบรวมรายงานสรุปขั้นสุดท้าย..."):
            summary_instruction = "คุณคือ CEO จงสรุปรายงานแผนงานจากทีมต่างๆ ให้กระชับ สละสลวย และเห็นภาพรวมการขับเคลื่อนองค์กร"
            summary_prompt = f"โจทย์หลัก: {user_input} \n\nโปรดสรุปภาพรวมจากงานที่มอบหมายไป"
            final_summary = ask_gemini(summary_instruction, summary_prompt)
            
            st.markdown("## 👑 บทสรุปผู้บริหาร (Executive Summary)")
            st.success(final_summary)
