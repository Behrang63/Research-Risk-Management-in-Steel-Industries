import sys
import os

# --- تضمین حل پویای مسیرهای ماژول‌ها (Module Resolution Guardrail) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

agents_dir = os.path.join(current_dir, "agents")
if os.path.exists(agents_dir) and agents_dir not in sys.path:
    sys.path.insert(0, agents_dir)

import streamlit as st
import json
import time
from typing import Dict, Any

# وارد کردن ایمن عامل‌های هوشمند
try:
    from agents.workflow_orchestrator import ProposalWorkflowOrchestrator
    from agents.analyzer_agent import ProposalAnalyzerAgent
    from agents.checker_agent import CheckerAgent
except ImportError:
    from workflow_orchestrator import ProposalWorkflowOrchestrator
    from analyzer_agent import ProposalAnalyzerAgent
    from checker_agent import CheckerAgent

# --- تنظیمات اولیه صفحه در Streamlit ---
st.set_page_config(
    page_title="سامانه ارزیابی هوشمند نوآوری تافکو (پژوهشیار AI)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- اعمال استایل CSS برای راست‌چین (RTL) و فونت فارسی ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stSidebar"], .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span, button {
        font-family: 'Vazirmatn', sans-serif !important;
        text-align: right !important;
        direction: RTL !important;
    }
    .stTextArea textarea {
        text-align: right !important;
        direction: RTL !important;
        font-family: 'Vazirmatn', sans-serif !important;
    }
    div.stButton > button:first-child {
        background-color: #D35400;
        color: white;
        font-weight: bold;
        width: 100%;
        border-radius: 8px;
        border: none;
        height: 3em;
        font-size: 16px;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #E67E22;
        color: white;
    }
    .metric-card {
        background-color: #1a252f;
        padding: 15px;
        border-radius: 10px;
        border-right: 5px solid #D35400;
        text-align: right;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- بارگذاری نمونه پروپوزال پیش‌فرض ---
DEFAULT_PROPOSAL = """موضوع پروپوزال: بومی‌سازی کاتالیست‌های نیکلی ریفرمر مدول‌های احیاء مستقیم (روش میدرکس) هلدینگ فولاد خوزستان

شرح فنی پروژه:
کاتالیست‌های ریفرمر از اجزای استراتژیک تولید گاز احیایی (مخلوط CO و H2) در کارخانجات احیاء مستقیم هستند. در این طرح ما با فرمولاسیون جدید پایه کاتالیست (آلومینای فعال شده با ارتقادهنده‌های قلیایی خاکی) موفق به کاهش پدیده مخرب رسوب کربن (Coking) شده‌ایم. این فناوری منجر به افزایش بازده حرارتی ریفرمر و کاهش حداقل ۲.۵ درصدی مصرف گاز طبیعی در فرآیند تولید آهن اسفنجی (DRI) می‌شود.

سطح بلوغ فناوری (TRL):
تیم پژوهشی ما نمونه‌های کاتالیست را در مقیاس آزمایشگاهی (راکتور بنچ‌تاپ با جریان مداوم) به مدت ۱۰۰ ساعت تست کرده و پایداری شیمیایی آن را اثبات نموده است (ادعای TRL 4). ما آمادگی داریم با حمایت تافکو، نمونه نیمه‌صنعتی (Pilot-scale) را تولید و در یکی از لوله‌های ریفرمر مدول زمزم تست کنیم.

برآورد بودجه:
مبلغ پیش‌بینی شده برای فاز نیمه‌صنعتی معادل ۵ میلیارد ریال است."""

# --- تعریف مسیر لوگوی محلی ---
logo_path = os.path.join(current_dir, "images", "ris_logo.jpg")

# --- بخش سایدبار (تنظیمات فنی) ---
with st.sidebar:
    # بررسی وجود فایل لوگو و بارگذاری محلی آن
    if os.path.exists(logo_path):
        st.image(logo_path, width=180)
    else:
        st.markdown("### 🏢 سیستم ارزیابی و مدیریت ریسک")
        
    st.markdown("---")
    st.markdown("### ⚙️ پیکربندی سیستمیک")
    
    model_name = st.selectbox(
        "انتخاب مدل زبانی (LLM Engine)",
        ["llama3.2", "llama3:latest", "llama3"],
        index=0
    )
    max_retries = st.slider("حداکثر چرخه اصلاح خودکار (Self-Correction)", 1, 5, 3)
    
    st.markdown("---")
    st.markdown("""
    **معماری حلقه بسته (Closed-loop):**
    این سیستم از یک معماری Agentic استفاده می‌کند. خروجی‌ها تا زمانی که توسط فیلترهای قطعی تایید نشوند، در یک لوپ بازخورد تصحیح می‌شوند.
    """)

# --- هدر اصلی نرم‌افزار ---
st.title("🤖 دستیار هوشمند غربالگری و ارزیابی نوآوری تافکو")
st.subheader("زیرسیستم ارزیابی قطعی پیشران‌ها و سنجش سطح بلوغ فناوری (TRL)")
st.markdown("---")

# --- بدنه اصلی ورود داده‌ها ---
st.markdown("#### 📝 متن پروپوزال پژوهشی یا طرح بومی‌سازی را وارد کنید:")
proposal_input = st.text_area(
    "پروپوزال را اینجا کپی کنید یا دکمه «اجرای ارزیابی سیستمی» را بزنید:",
    value=DEFAULT_PROPOSAL,
    height=250
)

col_actions = st.columns([1, 4])
with col_actions[0]:
    start_btn = st.button("🚀 اجرای ارزیابی سیستمی")

# --- اجرای خط لوله هوش مصنوعی (Pipeline execution) ---
if start_btn:
    if not proposal_input.strip() or len(proposal_input.strip()) < 50:
        st.error("❌ لطفا ابتدا یک پروپوزال معتبر و با جزئیات کافی فنی (حداقل ۵۰ کاراکتر) وارد کنید.")
    else:
        # مدیریت کامل استثناها برای جلوگیری از کرش کردن WebSocket و قطع شدن سرور
        try:
            with st.status("🔄 در حال اجرای معماری حلقه بسته (Orchestration Loop)...", expanded=True) as status:
                st.write("در حال پیکربندی عامل‌ها و تزریق شواهد قطعی...")
                
                # نمونه‌سازی یکپارچه از ارکستراتور و تزریق مستقیم مدل
                orchestrator = ProposalWorkflowOrchestrator(max_retries=max_retries, model_name=model_name)
                
                st.write(f"ارسال درخواست به موتور تحلیلی (حداکثر {max_retries} تلاش مجاز)...")
                
                # اجرای تابع اصلی ارکستراتور
                result = orchestrator.process_proposal(proposal_input)
                
                if result.get("status") == "success":
                    status.update(label=f"✅ پردازش پس از {result.get('attempts', 1)} چرخه با موفقیت پایان یافت.", state="complete", expanded=False)
                else:
                    status.update(label="❌ پردازش با شکست مواجه شد.", state="error", expanded=True)

            # --- تحلیل و نمایش نتایج بر اساس خروجی ارکستراتور ---
            if result.get("status") == "success":
                st.success(f"🎉 خروجی با موفقیت از سدهای قطعی و منطقی ممیز عبور کرد (تعداد چرخه‌های اجرا: {result.get('attempts')}).")
                # ایزوله‌سازی داده‌های نهایی جهت جلوگیری از TypeError یا AttributeError
                final_output = result.get("final_data") or {}
                
            elif result.get("status") == "failed":
                st.error("🚨 **عدم پایداری در پاسخ هوش مصنوعی (توقف سیستم)**")
                st.warning(f"موتور هوش مصنوعی پس از {result.get('attempts')} تلاش نتوانست خروجی استانداردی تولید کند.")
                st.error(f"دلیل رد شدن در آخرین تلاش: {result.get('last_rejection_reason')}")
                
                with st.expander("🛠️ مشاهده داده‌های ناقص (جهت دیباگ)"):
                    st.json(result.get("partial_data", {}))
                st.stop()
                
            else:
                st.error("خطای بحرانی در گردش کار سیستم رخ داده است.")
                st.stop()
                
            # --- داشبورد نتایج (Render Dashboard) ---
            st.markdown("### 📊 داشبورد نتایج غربالگری طرح")
            
            col_metrics = st.columns(3)
            
            # کارت ۱: امتیاز کل
            overall_score = final_output.get("weighted_overall_score", 0)
            with col_metrics[0]:
                st.markdown(f"""
                <div class="metric-card">
                    <span style="font-size:14px;color:#aaa;">امتیاز انطباق استراتژیک (وزن‌دار)</span>
                    <h2 style="margin:5px 0;color:#E67E22;">{overall_score} / 100</h2>
                </div>
                """, unsafe_allow_html=True)
                
            # کارت ۲: ارزیابی TRL
            trl_info = final_output.get("trl_analysis") or {}
            assessed_trl = trl_info.get("assessed_trl", "مشخص نشده")
            with col_metrics[1]:
                st.markdown(f"""
                <div class="metric-card" style="border-right-color:#2980b9;">
                    <span style="font-size:14px;color:#aaa;">سطح بلوغ فناوری (TRL) ارزیابی‌شده</span>
                    <h2 style="margin:5px 0;color:#3498db;">{assessed_trl}</h2>
                </div>
                """, unsafe_allow_html=True)
                
            # کارت ۳: توصیه نهایی
            recommendation = final_output.get("final_recommendation", "نیازمند بررسی")
            rec_color = "#27ae60" if "تایید" in str(recommendation) else ("#f39c12" if "اصلاح" in str(recommendation) else "#c0392b")
            with col_metrics[2]:
                st.markdown(f"""
                <div class="metric-card" style="border-right-color:{rec_color};">
                    <span style="font-size:14px;color:#aaa;">توصیه نهایی سیستم</span>
                    <h2 style="margin:5px 0;color:{rec_color};">{recommendation}</h2>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("---")
            
            # تب‌های گزارش
            tab_summary, tab_drivers, tab_critique, tab_raw = st.tabs([
                "📋 خلاصه و اقدامات اصلاحی", 
                "🎯 تحلیل انطباق با پیشران‌ها", 
                "⚠️ نقد فنی و شکاف TRL", 
                "💻 داده‌های خام ساختاریافته"
            ])
            
            with tab_summary:
                st.markdown("### خلاصه مدیریتی طرح")
                summary_data = final_output.get("proposal_summary") or {}
                st.info(summary_data.get("executive_summary", "خلاصه‌ای یافت نشد."))
                
                st.markdown("### 💡 بازخورد و راهکارهای ارتقای طرح برای مجری")
                st.warning(final_output.get("actionable_feedback_for_proposer", "بازخوردی برای این طرح ثبت نشده است."))
                
            with tab_drivers:
                st.markdown("### انطباق با پیشران‌های استراتژیک تافکو / فولاد خوزستان")
                alignments = final_output.get("strategic_alignment", [])
                
                if alignments and isinstance(alignments, list):
                    for idx, align in enumerate(alignments):
                        if isinstance(align, dict):
                            with st.expander(f"📌 پیشران {idx+1}: {align.get('driver_title', 'بدون عنوان')}"):
                                st.write(f"**شناسه پیشران:** `{align.get('driver_id')}`")
                                st.write(f"**امتیاز همراستایی مستقیم:** `{align.get('direct_alignment_score')}%`")
                                st.markdown(f"**📝 بند استنادی قطعی از پروپوزال (مدرک عدم توهم):**")
                                st.success(f"« {align.get('reasoning_quote', 'سندی یافت نشد')} »")
                else:
                    st.write("این طرح با هیچ‌کدام از پیشران‌های استراتژیک همراستایی ملموسی ندارد.")
                    
            with tab_critique:
                critique = final_output.get("technical_critique") or {}
                col_critique = st.columns(2)
                
                with col_critique[0]:
                    st.markdown("#### ✅ نقاط قوت فنی طرح")
                    strengths = critique.get("strengths", [])
                    if strengths:
                        for s in strengths:
                            st.write(f"• {s}")
                    else:
                        st.write("نقطه قوت مشخصی استخراج نشده است.")
                        
                with col_critique[1]:
                    st.markdown("#### ❌ ریسک‌ها و نقاط ضعف پنهان (بدبینی مهندسی)")
                    weaknesses = critique.get("weaknesses_and_risks", [])
                    if weaknesses:
                        for w in weaknesses:
                            st.write(f"• {w}")
                    else:
                        st.write("ریسک حادی یافت نشد.")
                
                st.markdown("---")
                st.markdown("#### 🚩 ابهامات و پرچم‌های قرمز (Red Flags)")
                red_flags = critique.get("red_flags", [])
                if red_flags:
                    for r in red_flags:
                        st.write(f"⚠️ {r}")
                else:
                    st.write("مورد مبهمی یافت نشد.")
                    
                st.markdown("---")
                st.markdown("#### 📈 تحلیل شکاف TRL (TRL Gap Analysis)")
                st.write(f"**TRL ادعایی مجری:** {trl_info.get('claimed_trl', 'ذکر نشده')}")
                st.write(f"**TRL واقعی ارزیابی‌شده:** {trl_info.get('assessed_trl', 'مشخص نشده')}")
                st.info(trl_info.get("gap_analysis", "تحلیل شکاف TRL تولید نشده است."))
                
            with tab_raw:
                st.markdown("### خروجی JSON (آماده برای یکپارچه‌سازی با پایگاه داده سامانه پژوهشیار)")
                st.markdown("این داده‌ها پس از عبور از فیلترهای قطعی تولید شده‌اند.")
                st.json(final_output)

        except Exception as e:
            # نمایش دقیق خطا در محیط رابط کاربری بدون قطع شدن اتصال سرور
            st.error("🚨 **خطای ناخواسته در اجرای پردازش:**")
            st.code(str(e), language="python")
            st.info("💡 **راهنمایی دیباگ:** بررسی کنید که سرویس Ollama روشن باشد و مدل انتخاب‌شده دانلود شده باشد.")