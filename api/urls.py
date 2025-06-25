from django.urls import path
from . import views

from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

urlpatterns = [
    # AUTH URLS
    path('user/token/', views.MyTokenObtainPairView.as_view()),
    path('user/token/refresh/', TokenRefreshView.as_view()),
    path('user/register/', views.RegisterAPIView.as_view()),


    # PASSWORD RESET URLS
    path('user/password-reset/', views.PasswordResetAPIView.as_view()),
    path('user/password-reset/<email>/', views.PasswordResetEmailVerifyAPIView.as_view()),
    path('user/change-password/', views.ChangePasswordAPIView.as_view()),

    # PROFILE URL
    path('user/profile/<str:user_id>/', views.ProfileAPIView.as_view()),


    # CATEGORY URLS
    path('course/category/', views.CategoryListAPIView.as_view()),


    # COURSE URLS
    path('course/course-list/', views.CourseListAPIView.as_view()),
    path('course/course-detail/<slug:slug>/', views.CourseDetailAPIView.as_view()),
    path('course/search/', views.SearchCourseAPIView.as_view()),


    # CART URLS
    path('course/cart/', views.CartAPIView.as_view()),
    path('course/cart-list/<str:cart_id>/', views.CartListAPIView.as_view()),
    path('course/cart-item-delete/<cart_id>/<item_id>/', views.CartItemDeleteAPIView.as_view()),
    path('course/cart-details/<cart_id>/', views.CartStatsAPIView.as_view()),


    # ORDER URLS
    path('order/create-order/', views.CreateOrderAPIView.as_view()),
    path('order/delete-order/<oid>/', views.DeleteOrderAPIView.as_view()),
    path('order/checkout/<oid>/', views.CheckOutAPIView.as_view()),
    path('order/coupon/', views.CouponApplyAPIView.as_view()),


    # PAYMENT URLS
    path('payment/stripe-chekout/<str:order_oid>/', views.StripeCheckoutAPIView.as_view()),
    path('payment/payment-success/', views.PaymentSuccessAPIView.as_view()),
    

    # STUDENT URLS
    path('student/summary/<str:user_id>/', views.StudentSummaryAPIView.as_view()),
    path('student/course-list/<str:user_id>/', views.StudentCourseListAPIView.as_view()),
    path('student/course-details/<str:enrollment_id>/', views.StudentCourseDetailsAPIView.as_view()),
    path('student/course-completed/', views.StudentCourseCompletedAPIView.as_view()),
    path('student/wishlist/<str:user_id>/', views.StudentWishlistAPIView.as_view()),
    path('student/course-note/', views.StudentNoteCreateAPIView.as_view()),
    path('student/course-note-detail/<str:user_id>/<str:note_id>/', views.StudentNoteDetailAPIView.as_view()),
    path('student/rate-course/', views.StudentRateCourseCreateAPIView.as_view()),
    path('student/review-detail/<str:user_id>/<review_id>/', views.StudentRateCourseUpdateAPIView.as_view()),
    path('student/question-answer-list-create/', views.QuestionAnswerListCreateAPIView.as_view()),
    path('student/question-answer-message-create/', views.QuestionAnswerMessageSendAPIView.as_view()),


    # TEACHER URLS
    path('teacher/details/<str:id>/', views.TeacherDetailsAPIView.as_view()),
    path('teacher/courses/<str:teacher_id>/', views.TeacherCourseWithCourseIdAPIView.as_view()),
    path('teacher/summary/<str:teacher_id>/', views.TeacherSummaryAPIView.as_view()),
    path('teacher/course-list/<str:teacher_id>/', views.TeacherCourseListAPIView.as_view()),
    path('teacher/review-list/<str:teacher_id>/', views.TeacherReviewListAPIView.as_view()),
    path('teacher/review-detail/<str:teacher_id>/<str:review_id>/', views.TeacherReviewDetailAPIView.as_view()),
    path('teacher/student-list/<str:teacher_id>/', views.TeacherStudentsListAPIView.as_view({'get' : 'list'})),
    path('teacher/month-wise-revenue/<str:teacher_id>/', views.TeacherAllMonthEarningAPIView.as_view()),
    path('teacher/best-selling-course/<str:teacher_id>/', views.TeacherBestSellingCourseAPIView.as_view()),
    path('teacher/course-order-list/<str:teacher_id>/', views.TeacherCourseOrderListAPIView.as_view()),
    path('teacher/course-question-answer-list/<str:teacher_id>/', views.TeacherQuestionAnswerListAPIView.as_view()),
    path('teacher/coupon-list/<str:teacher_id>/', views.TeacherCouponListCreateAPIView.as_view()),
    path('teacher/coupon-list-detail/<str:teacher_id>/<str:coupon_id>/', views.TeacherCouponDetailAPIView.as_view()),
    path('teacher/notification-list/<str:teacher_id>/', views.TeacherNotificationListAPIView.as_view()),
    path('teacher/notification-detial/<str:teacher_id>/<str:notification_id>/', views.TeacherNotificationDetailAPIView.as_view()),
    path('teacher/course-create/<str:teacher_id>/', views.CourseCreateAPIView.as_view()),
    


    # EXTRA URLS
    path('user/enrollment-course-id/<str:user_id>/', views.StudentEnrollmentAndCourseIDAPIView.as_view()),
    path('file-upload/', views.FileUploadAPIView.as_view())

]
