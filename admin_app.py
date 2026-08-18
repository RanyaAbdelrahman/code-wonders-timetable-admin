import secrets
from datetime import date

import streamlit as st
from supabase import create_client


# ============================================================
# إعداد الصفحة
# ============================================================

st.set_page_config(
    page_title="🔐 لوحة إدارة نظام الجداول المدرسية",
    page_icon="🔐",
    layout="centered",
)

APP_VERSION = "ADMIN-PANEL-2026-08-18"


# ============================================================
# قراءة Streamlit Secrets
# ============================================================

try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    ADMIN_PASSWORD = st.secrets["supabase"]["ADMIN_PASSWORD"]
    SERVICE_ROLE_KEY = st.secrets["supabase"]["SUPABASE_SERVICE_ROLE_KEY"]

except Exception as e:
    st.error(
        "❌ تعذر قراءة Streamlit Secrets.\n\n"
        "تأكد من وجود القيم التالية داخل [supabase]:\n\n"
        "[supabase]\n"
        'url = "https://....supabase.co"\n'
        'key = "sb_publishable_..."\n'
        'ADMIN_PASSWORD = "..."\n'
        'SUPABASE_SERVICE_ROLE_KEY = "sb_secret_..."\n\n'
        f"التفاصيل: {e}"
    )
    st.stop()


if not str(ADMIN_PASSWORD).strip():
    st.error("❌ ADMIN_PASSWORD فارغة داخل Streamlit Secrets.")
    st.stop()


if not str(SERVICE_ROLE_KEY).strip():
    st.error("❌ SUPABASE_SERVICE_ROLE_KEY فارغة داخل Streamlit Secrets.")
    st.stop()


# ============================================================
# الاتصال بـ Supabase
# ============================================================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)

admin_supabase = create_client(
    SUPABASE_URL,
    SERVICE_ROLE_KEY,
)


# ============================================================
# دوال الإدارة
# ============================================================

def generate_license_key():
    """
    إنشاء License Key جديد.
    """
    return "CW-" + secrets.token_hex(8).upper()


def admin_schools():
    """
    قراءة جميع المدارس من جدول Schools.
    """
    result = (
        admin_supabase
        .table("Schools")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return result.data or []


def admin_update_school(school_id, values):
    """
    تعديل بيانات مدرسة.
    """
    return (
        admin_supabase
        .table("Schools")
        .update(values)
        .eq("id", school_id)
        .execute()
    )


def save_license(school_id, start_date, expiry_date):
    """
    اعتماد المدرسة أو تجديد الترخيص.
    ويحافظ على License Key الموجود إن كان موجودًا.
    """

    current = (
        admin_supabase
        .table("Schools")
        .select("license_key")
        .eq("id", school_id)
        .limit(1)
        .execute()
    )

    current_data = current.data[0] if current.data else {}

    license_key = (
        current_data.get("license_key")
        or generate_license_key()
    )

    return (
        admin_supabase
        .table("Schools")
        .update(
            {
                "status": "approved",
                "start_date": str(start_date),
                "expiry_date": str(expiry_date),
                "license_key": license_key,
            }
        )
        .eq("id", school_id)
        .execute()
    )


# ============================================================
# تصميم الصفحة
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
        linear-gradient(
            135deg,
            #f0f4f8 0%,
            #d9e2ec 100%
        );

        font-family:
        'Cairo',
        'Segoe UI',
        Tahoma,
        sans-serif;
    }


    .admin-header {

        background:
        linear-gradient(
            135deg,
            #312e81 0%,
            #7c3aed 100%
        );

        padding: 30px;

        border-radius: 20px;

        color: white;

        text-align: center;

        margin-bottom: 25px;
    }


    .admin-header h1 {

        font-size: 30px;

        font-weight: 800;

        margin-bottom: 10px;
    }


    .admin-header p {

        font-size: 16px;

        margin: 0;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="admin-header">

        <h1>
            🔐 لوحة إدارة نظام الجداول المدرسية
        </h1>

        <p>
            Code Wonders Academy
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# تسجيل دخول الإدارة
# ============================================================

if "admin_logged_in" not in st.session_state:

    st.session_state.admin_logged_in = False


if not st.session_state.admin_logged_in:

    st.markdown("## 🔐 دخول الإدارة")

    password = st.text_input(
        "كلمة مرور الإدارة",
        type="password",
        placeholder="أدخل كلمة مرور الإدارة",
    )


    if st.button(
        "🔓 دخول",
        use_container_width=True,
    ):

        if password == ADMIN_PASSWORD:

            st.session_state.admin_logged_in = True

            st.rerun()

        else:

            st.error(
                "❌ كلمة مرور الإدارة غير صحيحة."
            )


    st.caption(
        f"الإصدار: {APP_VERSION}"
    )

    st.stop()


# ============================================================
# بعد تسجيل الدخول
# ============================================================

col1, col2 = st.columns(
    [4, 1]
)


with col1:

    st.success(
        "✅ تم تسجيل الدخول إلى لوحة الإدارة."
    )


with col2:

    if st.button(
        "🚪 خروج",
        use_container_width=True,
    ):

        st.session_state.admin_logged_in = False

        st.rerun()


# ============================================================
# قراءة المدارس
# ============================================================

try:

    schools = admin_schools()

except Exception as e:

    st.error(
        f"❌ تعذر قراءة جدول Schools: {e}"
    )

    st.stop()


# ============================================================
# الإحصائيات
# ============================================================

total = len(schools)

pending = sum(
    1
    for school in schools
    if (school.get("status") or "pending") == "pending"
)

approved = sum(
    1
    for school in schools
    if (school.get("status") or "") == "approved"
)

rejected = sum(
    1
    for school in schools
    if (school.get("status") or "") == "rejected"
)

blocked = sum(
    1
    for school in schools
    if (school.get("status") or "") == "blocked"
)


# ============================================================
# عرض الإحصائيات
# ============================================================

st.markdown("## 📊 إحصائيات النظام")


c1, c2, c3, c4, c5 = st.columns(5)


with c1:
    st.metric(
        "إجمالي المدارس",
        total
    )


with c2:
    st.metric(
        "قيد المراجعة",
        pending
    )


with c3:
    st.metric(
        "مفعلة",
        approved
    )


with c4:
    st.metric(
        "مرفوضة",
        rejected
    )


with c5:
    st.metric(
        "موقوفة",
        blocked
    )


st.divider()


# ============================================================
# تحديث البيانات
# ============================================================

if st.button(
    "🔄 تحديث البيانات",
    use_container_width=True,
):

    st.rerun()


# ============================================================
# قائمة المدارس
# ============================================================

st.markdown(
    "## 📋 المدارس المسجلة"
)


if not schools:

    st.info(
        "لا توجد مدارس مسجلة حتى الآن."
    )

else:

    for school in schools:

        school_id = school.get("id")

        school_name = (
            school.get("school_name")
            or "بدون اسم"
        )

        email = (
            school.get("email")
            or ""
        )

        phone = (
            school.get("phone")
            or ""
        )

        status = (
            school.get("status")
            or "pending"
        )

        start_raw = school.get(
            "start_date"
        )

        expiry_raw = school.get(
            "expiry_date"
        )

        license_key = (
            school.get("license_key")
            or "-"
        )


        # ====================================================
        # مدرسة
        # ====================================================

        with st.expander(
            f"🏫 {school_name} — {status.upper()}"
        ):

            st.write(
                f"**Email:** {email}"
            )

            st.write(
                f"**Phone:** {phone}"
            )

            st.write(
                f"**Status:** {status}"
            )

            st.write(
                f"**License:** `{license_key}`"
            )


            # ================================================
            # التواريخ
            # ================================================

            try:

                start_default = (
                    date.fromisoformat(
                        str(start_raw)[:10]
                    )
                    if start_raw
                    else date.today()
                )

            except Exception:

                start_default = date.today()


            try:

                expiry_default = (
                    date.fromisoformat(
                        str(expiry_raw)[:10]
                    )
                    if expiry_raw
                    else date.today()
                )

            except Exception:

                expiry_default = date.today()


            st.markdown(
                "### 📅 إعداد الترخيص"
            )


            d1, d2 = st.columns(2)


            with d1:

                new_start = st.date_input(
                    "بداية الترخيص",
                    value=start_default,
                    key=f"admin_start_{school_id}",
                )


            with d2:

                new_expiry = st.date_input(
                    "نهاية الترخيص",
                    value=expiry_default,
                    key=f"admin_expiry_{school_id}",
                )


            # ================================================
            # أزرار الإدارة
            # ================================================

            a, b, c = st.columns(3)


            with a:

                if st.button(
                    "✅ اعتماد",
                    key=f"admin_approve_{school_id}",
                    use_container_width=True,
                ):

                    if new_expiry < new_start:

                        st.error(
                            "❌ تاريخ الانتهاء يجب أن يكون بعد تاريخ البداية."
                        )

                    else:

                        try:

                            save_license(
                                school_id,
                                new_start,
                                new_expiry,
                            )

                            st.success(
                                "✅ تم اعتماد المدرسة وتفعيل الترخيص."
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                f"❌ خطأ أثناء الاعتماد: {e}"
                            )


            with b:

                if st.button(
                    "❌ رفض",
                    key=f"admin_reject_{school_id}",
                    use_container_width=True,
                ):

                    try:

                        admin_update_school(
                            school_id,
                            {
                                "status": "rejected"
                            },
                        )

                        st.success(
                            "✅ تم رفض الطلب."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"❌ خطأ: {e}"
                        )


            with c:

                if st.button(
                    "⛔ إيقاف",
                    key=f"admin_block_{school_id}",
                    use_container_width=True,
                ):

                    try:

                        admin_update_school(
                            school_id,
                            {
                                "status": "blocked"
                            },
                        )

                        st.success(
                            "⛔ تم إيقاف ترخيص المدرسة."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"❌ خطأ: {e}"
                        )


# ============================================================
# Footer
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        padding:25px 15px;
        color:#4f46e5;
        font-weight:bold;
    ">

        Code Wonders Academy

        <br>

        لوحة إدارة نظام الجداول المدرسية

    </div>
    """,
    unsafe_allow_html=True,
)
