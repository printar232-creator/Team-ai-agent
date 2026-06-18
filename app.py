import streamlit as st
import google.generativeai as genai
import json
import asyncio

# --- 1. CONFIG & INITIALIZATION ---
st.set_page_config(page_title="AI Team Enterprise System", page_icon="🤖", layout="wide")

# ดึง API Key จาก Streamlit Secrets (สำหรับรันบน Cloud/GitHub)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("❌ ไม่พบ GEMINI_API_KEY ใน Streamlit Secrets! กรุณาตั้งค่าก่อนใช้งาน")
    st.stop()

# --- 2. DEFINING THE AGENTS (PROMPTS) ---
TEAMS_INFO = {
    "Production": "ดูแลเรื่องกระบวนการผลิต การวางแผนโรงงาน สินค้าคงคลัง และ Supply Chain",
    "Lab": "ดูแลเรื่องการวิจัยและพัฒนา (R&D) การทดลอง สูตรเคมี/ผลิตภัณฑ์ และการควบคุมคุณภาพ (QC)",
    "HR": "ดูแลเรื่องทรัพยากรบุคคล การจัดจ้าง การประเมินผล สวัสดิการ และการอบรมพนักงาน",
    "Account": "ดูแลเรื่องการเงิน บัญชี งบประมาณ รายรับ-รายจ่าย และความคุ้มทุน"
}

# --- 3. HELPER FUNCTIONS ---
def ask_gemini_sync(system_instruction, prompt):
    """ฟังก์ชันทำงานแบบปกติ (Sync) สำหรับผู้บริหาร/Manager ในการวิเคราะห์ขั้นแรก"""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}"

async def ask_gemini_async(system_instruction, prompt):
    """ฟังก์ชันทำงานแบบขนาน (Async) สำหรับแต่ละทีมย่อย เพื่อความรวดเร็วขั้นสุด"""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction
        )
        # เรียกใช้ API แบบไม่รอต่อคิว (Asynchronous)
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}"

def manager_delegate(user_task):
    """สมองส่วนกลาง (Manager) วิเคราะห์แยกงานให้กับทีม"""
    manager_instruction = (
        "คุณคือ CEO และ Manager AI อัจฉริยะ ทำหน้าที่รับบรีฟงานจากผู้ใช้ "
        "แล้ววิเคราะห์ว่างานนี้จำเป็นต้องส่งต่อให้ทีมใดใน 4 ทีมนี้บ้าง: Production, Lab, HR, Account "
        "คุณต้องตอบกลับเป็นรูปแบบ JSON Array เท่านั้น เช่น ['Production', 'Lab'] "
        "วิเคราะห์ให้ดีว่างานเกี่ยวพันกับทีมไหนบ้าง (สามารถตอบได้มากกว่า 1 ทีม หรือตอบทั้งหมดหากเกี่ยวข้องกันทั้งหมด) "
        "ห้ามอธิบายข้อความอื่นนอกเหนือจาก JSON format เด็ดขาด"
    )
    
    prompt = f"งานที่ได้รับ: '{user_task}' \n\nทีมที่มีอยู่: {json.dumps(TEAMS_INFO, ensure_ascii=False)}"
    response_text = ask_gemini_sync(manager_instruction, prompt)
    
    # ทำความสะอาดข้อมูลสตริง เผื่อกรณีโมเดลใส่ markdown code block มา
    clean_text = response_text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean_text)
    except:
        # Fallback หากแปลง JSON ล้มเหลว ให้ส่งงานให้ทุกทีมช่วยกันดู
        return list(TEAMS_INFO.keys())

async def run_all_teams(assigned_teams, user_input):
    """ฟังก์ชันควบคุมการรันงานพร้อมกันทุกทีมในเวลาเดียวกัน"""
    tasks = []
    for team_name in assigned_teams:
        team_instruction = (
            f"คุณคือหัวหน้าทีม {team_name} ที่เชี่ยวชาญระดับโลก หน้าที่ของคุณคือ: {TEAMS_INFO[team_name]} \n"
            f"จงวิเคราะห์ข้อสรุป แนวทางปฏิบัติ หรือวิธีแก้ปัญหาในมุมมองของทีมคุณจากโจทย์ที่ได้รับ \n"
            f"ข้อกำหนดสำคัญ: เน้นเนื้อหาที่สั้น กระชับ จับต้องได้ นำไปใช้จริงได้ทันที สรุปเป็นข้อๆ ไม่เกิน 4 ข้อ และห้ามพิมพ์ยาวเวิ่นเว้อ"
        )
        # สร้าง Task เตรียมไว้ แต่ยังไม่สั่งรัน
        tasks.append(ask_gemini_async(team_instruction, user_input))
    
    # สั่งให้ทุก Task ทำงานขนานพร้อมๆ กันและรอผลลัพธ์กลับมาพร้อมกัน
    return await asyncio.gather(*tasks)

# --- 4. STREAMLIT UI ---
st.title("🤖 Enterprise AI Team Network (⚡ High-Speed Version)")
st.subheader("ระบบบริหารงานอัตโนมัติด้วยสมองส่วนกลาง Gemini ทำงานแบบขนาน")
st.write("---")

# ส่วนรับ Input จากผู้ใช้
user_input = st.text_area(
    "📥 ใส่โจทย์หรือคำสั่งงานที่ต้องการให้ทีม AI ช่วยกันคิด:",
    placeholder="เช่น 'เราต้องการผลิตเครื่องดื่มชูกำลังรสชาติใหม่เพื่อเจาะตลาดวัยรุ่น ต้องเตรียมตัวอย่างไรบ้าง'"
)

if st.button("🚀 สั่งการทีม AI (รันแบบขนาน)", type="primary"):
    if user_input.strip() == "":
        st.warning("กรุณากรอกคำสั่งงานก่อนครับ")
    else:
        # --- ขั้นตอนที่ 1: Manager วิเคราะห์แยกงาน ---
        with st.spinner("🧠 สมองส่วนกลาง (Gemini Manager) กำลังวิเคราะห์และแจกจ่ายงาน..."):
            assigned_teams = manager_delegate(user_input)
        
        st.success(f"📋 **Manager สั่งการ:** มอบหมายงานนี้ให้แก่ทีม: {', '.join(assigned_teams)}")
        st.write("---")
        
        # --- ขั้นตอนที่ 2: ให้ทีมที่ได้รับมอบหมายทำงานพร้อมกัน (Async) ---
        with st.spinner("⚡ ทุกทีมกำลังระดมสมองพร้อมกันในเวลาเดียวกัน (Parallel Processing)..."):
            # เรียกใช้ฟังก์ชันรันขนานผ่าน asyncio.run()
            results = asyncio.run(run_all_teams(assigned_teams, user_input))
        
        # แสดงผลลัพธ์แยกตามคอลัมน์ของแต่ละทีม
        cols = st.columns(len(assigned_teams))
        for idx, team_name in enumerate(assigned_teams):
            with cols[idx]:
                st.markdown(f"### 🏢 ทีม: {team_name}")
                st.caption(TEAMS_INFO[team_name])
                # แสดงข้อมูลสรุปสั้นที่ได้จาก List ผลลัพธ์
                st.info(results[idx])

        # --- ขั้นตอนที่ 3: สรุปรวมแผนงานจากผู้บริหาร ---
        st.write("---")
        with st.spinner("📝 Manager กำลังรวบรวมรายงานสรุปขั้นสุดท้าย..."):
            summary_instruction = (
                "คุณคือ CEO จงสรุปรายงานแผนงานจากทีมต่างๆ ให้กระชับ สละสลวย "
                "และเห็นภาพรวมการเคลื่อนทัพขององค์กรในภาพใหญ่ สรุปให้จบภายใน 2-3 ย่อหน้า"
            )
            
            # รวบรวมคำตอบของทุกทีมเพื่อส่งให้ CEO อ่านสรุปอีกรอบ
            team_reports_combined = ""
            for idx, team_name in enumerate(assigned_teams):
                team_reports_combined += f"\n--- รายงานจากทีม {team_name} ---\n{results[idx]}\n"
                
            summary_prompt = f"โจทย์หลัก: {user_input} \n\nรายงานจากแต่ละทีมที่ส่งมามีดังนี้: \n{team_reports_combined}"
            final_summary = ask_gemini_sync(summary_instruction, summary_prompt)
            
            st.markdown("## 👑 บทสรุปผู้บริหาร (Executive Summary)")
            st.success(final_summary)
