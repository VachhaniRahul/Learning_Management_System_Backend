from django.contrib import admin

from .models import (
Teacher,
Category,
Course,
Variant,
VariantItem,
Question_Answer,
Question_Answer_Message,
Cart,
CartOrder,
CartOrderItem,
Certificate,
CompletedLesson,
EnrolledCourse,
Note,
Review,
Notification,
Coupon,
Wishlist,
Country
)


admin.site.register(Teacher)
admin.site.register(Category)
admin.site.register(Course)
admin.site.register(Variant)
admin.site.register(VariantItem)
admin.site.register(Question_Answer)
admin.site.register(Question_Answer_Message)
admin.site.register(Cart)
admin.site.register(CartOrder)
admin.site.register(CartOrderItem)
admin.site.register(Certificate)
admin.site.register(CompletedLesson)
admin.site.register(EnrolledCourse)
admin.site.register(Note)
admin.site.register(Review)
admin.site.register(Notification)
admin.site.register(Coupon)
admin.site.register(Wishlist)
admin.site.register(Country)

