from django.db import models
from django.utils.text import slugify
from shortuuid.django_fields import ShortUUIDField
from moviepy.editor import VideoFileClip
from userauths.models import User, Profile
import math
from django.utils import timezone

# Create your models here.

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.FileField(upload_to='teacher_file', default='default-teacher.jpg', blank=True, null=True)
    full_name = models.CharField(max_length=100)
    bio = models.CharField(max_length=1000, null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    twitter = models.URLField(null=True, blank=True)
    linkedIn = models.URLField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.full_name
    
    def students(self):
        return CartOrderItem.objects.filter(teacher = self, order__payment_status = 'Paid')
    
    def courses(self):
        return Course.objects.filter(teacher = self)
    
    def review(self):
        return Review.objects.filter(teacher = self)

class Category(models.Model):
    title = models.CharField(max_length=100)
    image = models.FileField(upload_to='category_file', default='category.jpg', null=True, blank=True)
    slug = models.SlugField(unique=True, null=True, blank=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title
    
    def course_count(self):
        return Course.objects.filter(category=self).count()
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Category, self).save(*args, **kwargs) 

class Course(models.Model):
    LANGUAGE  = (
        ('English', 'English'),
        ('Hindi', 'Hindi'),
        ('Spanish', 'Spanish'),
        ('Gujarati', 'Gujarati'),
    )

    LEVEL = (
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    )

    TEACHER_STATUS = (
        ('Draft', 'Draft'),
        ('Disable', 'Disable'),
        ('Published', 'Published'),
    )
    
    PLATEFORM_STATUS = (
        ('Review', 'Review'),
        ('Disable', 'Disable'),
        ('Rejected', 'Rejected'),
        ('Draft', 'Draft'),
        ('Published', 'Published'),
    )
    course_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet='1234567890')
    slug = models.SlugField(unique=True, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    file = models.FileField(upload_to='course_file', blank=True, null=True)
    image = models.FileField(upload_to='course_file', blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    language = models.CharField(choices=LANGUAGE, default='English', max_length=100)
    level = models.CharField(choices=LEVEL, default='Beginner', max_length=100)
    plateform_status = models.CharField(choices=PLATEFORM_STATUS, default='Published', max_length=100)
    teacher_status = models.CharField(choices=TEACHER_STATUS, default='Published', max_length=100)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Course, self).save(*args, **kwargs)

    def student_count(self):
        return EnrolledCourse.objects.filter(course = self).count()
    def students(self):
        return EnrolledCourse.objects.filter(course=self)
    
    def curriculum(self):
        return Variant.objects.filter(course = self)
    
    def lectures(self):
        return VariantItem.objects.filter(variant__course=self)
    
    def average_rating(self):
        average_rating = Review.objects.filter(course=self).aggregate(avg_rating=models.Avg('rating'))
        return average_rating

    def rating_count(self):
        return Review.objects.filter(course=self).count()
    
    def reviews(self):
        return Review.objects.filter(course=self)

class Variant(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000)
    variant_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet='1234567890')
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
    

    def variant_item(self):
        return VariantItem.objects.filter(variant=self)
    
class VariantItem(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='variant_items')
    title = models.CharField(max_length=1000)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='course_file')
    duration = models.DurationField(null=True, blank=True)
    content_duration = models.CharField(max_length=1000, null=True, blank=True)
    preview = models.BooleanField(default=False)
    variant_item_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet='1234567890')
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.variant.title} - {self.title}'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file:
            clip = VideoFileClip(self.file.path)
            duration_seconds = clip.duration

            minutes, rem = divmod(duration_seconds, 60)
            minutes = math.floor(minutes)
            seconds = math.floor(rem)
            duration_text = f'{minutes}m {seconds}s'
            self.content_duration = duration_text
            super().save(update_fields=['content_duration'])

class Question_Answer(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=1000, null=True, blank=True)
    qa_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet='1234567890')
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.username} - {self.course.title}'
    
    class Meta:
        ordering = ['-date']

    def messages(self):
        return Question_Answer_Message.objects.filter(question=self)
    
    def profile(self):
        return Profile.objects.filter(user=self.user).first()
    
class Question_Answer_Message(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question = models.ForeignKey(Question_Answer, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    is_teacher = models.BooleanField(default=False)
    qam_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet='1234567890')
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.username} - {self.course.title}'
    
    class Meta:
        ordering = ['date']

    def profile(self):
        return Profile.objects.get(user=self.user)

class Cart(models.Model):
    cart_id = ShortUUIDField(length=6, max_length=20, alphabet='1234567890')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cart')
    price = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    tax_fee = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    country = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
class CartOrder(models.Model):
    PAYMENT_STATUS = (
        ('Paid', 'Paid'),
        ('Processing', 'Processing'),
        ('Failed', 'Failed'),
    )
    student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ManyToManyField(Teacher, blank=True)
    sub_total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    tax_fee = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    initial_total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    saved = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    payment_status = models.CharField(max_length=100, choices=PAYMENT_STATUS, default='Processing')
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    country = models.CharField(max_length=100,null=True,blank=True)
    coupons = models.ManyToManyField('Coupon', blank=True)
    stripe_session_id = models.CharField(max_length=1000, null=True, blank=True)
    oid = ShortUUIDField(unique=True, length=6, max_length=20, alphabet='1234567890')
    cart_id = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']

    def order_item(self):
        return CartOrderItem.objects.filter(order=self)
    
    def __str__(self):
        return self.oid
    
class CartOrderItem(models.Model):
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE, related_name='orderitem')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='order_item')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    tax_fee = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    price = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    saved = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    initial_total = models.DecimalField(max_digits=12, default=0.00, decimal_places=2)
    coupons = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    applied_coupon = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']

    def order_id(self):
        return f'Order ID #{self.order.oid}'
    
    def payment_status(self):
        return self.order.payment_status
    
    def __str__(self):
        return self.order.oid 
    
class Certificate(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    certificate_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet='1234567890')
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
class CompletedLesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    variant_item = models.ForeignKey(VariantItem, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
class EnrolledCourse(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='enroll_courses')
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    order_item = models.ForeignKey(CartOrderItem, on_delete=models.CASCADE)
    enrollment_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet='1234567890')
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
       
    def lectures(self):
        return VariantItem.objects.filter(variant__course=self.course)
    
    def completed_lessons(self):
        return CompletedLesson.objects.filter(course=self.course, user=self.user)
    
    def curriculem(self):
        return Variant.objects.filter(course=self.course)
    
    def note(self):
        return Note.objects.filter(course=self.course, user=self.user)
    
    def question_answer(self):
        return Question_Answer.objects.filter(course=self.course)
    
    def review(self):
        return Review.objects.filter(course=self.course, user=self.user).first()
    
class Note(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    note_id= ShortUUIDField(unique=True, length=6, max_length=20, alphabet='1234567890')
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
    
class Review(models.Model):
    RATING = (
        (1, '1 Star'),
        (2, '2 Star'),
        (3, '3 Star'),
        (4, '4 Star'),
        (5, '5 Star'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    review = models.TextField()
    rating = models.IntegerField(choices=RATING, default=None)
    reply = models.CharField(max_length=1000,null=True, default=None)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.course.title
    
    def profile(self):
        return Profile.objects.get(user=self.user)
    
class Notification(models.Model):
    NOTI_TYPE = (
        ('New Order', 'New Order'),
        ('New Review', 'New Review'),
        ('New Course Question', 'New Course Question'),
        ('Course Published', 'Course Published'),
        ('Course Enrollment Completed', 'Course Enrollment Completed')
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(CartOrder, on_delete=models.SET_NULL, null=True, blank=True)
    order_item = models.ForeignKey(CartOrderItem, on_delete=models.SET_NULL, null=True, blank=True)
    review = models.ForeignKey(Review, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=100, choices=NOTI_TYPE)
    seen = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.type

class Coupon(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True,blank=True)
    used_by = models.ManyToManyField(User, blank=True)
    code = models.CharField(max_length=100)
    discount = models.IntegerField(default=1)
    date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.code
    
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.user.username
    
class Country(models.Model):
    name = models.CharField(max_length=100)
    tax_rate = models.IntegerField(default=1)

    def __str__(self):
        return self.name




    















    
