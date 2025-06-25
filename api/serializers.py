from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from userauths.models import User, Profile
from . import models as api_models


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        teacher = api_models.Teacher.objects.filter(user=user).first()
        if teacher:
            token['teacher_id'] = teacher.id
        else:
            token['teacher_id'] = None
        token['email'] = user.email
        token['username'] = user.username

        return token
    
    def validate(self, attrs):
        credentials = {
            'email': attrs.get('email'),
            'password': attrs.get('password')
        }

        user = authenticate(**credentials)

        if user is None:
            raise serializers.ValidationError({
                'detail': 'Invalid credentials'
            })

        data = super().validate(attrs)
        cart = self.user.cart.all()
        teacher = api_models.Teacher.objects.filter(user=self.user).first()
        if teacher:
            data['teacher_id'] = teacher.id
        
        if cart:
            data['cart_id'] = cart[0].cart_id
        else:
            data['cart_id'] = 'empty'
        
        # Add custom response data here
        data['user_id'] = self.user.id
        data['username'] = self.user.username
        data['email'] = self.user.email
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, max_length=200)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'password' : 'password and confirm_password fields didn\'t match'
            })
        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(
            full_name = validated_data['full_name'],
            email= validated_data['email'],
            username = validated_data['email'].split()[0],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user       

class PasswordResetSerializer(serializers.Serializer):
    otp = serializers.CharField()
    uuid64 = serializers.CharField()
    password = serializers.CharField()

class ChangePasswordSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    old_password = serializers.CharField()
    new_password = serializers.CharField()


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = '__all__'
        extra_kwargs = {
            'user': {'read_only': True}
        }


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Category
        fields = ['title', 'image', 'slug', 'course_count']

class TeacherSerializer(serializers.ModelSerializer):
    user = serializers.CharField(read_only= True)
    class Meta:
        model = api_models.Teacher
        fields = [
            'user', 'image', 'full_name', 'bio', 'facebook', 'twitter', 'linkedIn', 'about', 'country'
        ]


class VariantItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = api_models.VariantItem
        fields = '__all__'

class VariantSerializer(serializers.ModelSerializer):
    variant_item = VariantItemSerializer(many=True)
    class Meta:
        model = api_models.Variant
        fields = '__all__'





class QuestionAnswerMessagesSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.profile.full_name', read_only=True)
    profile = serializers.SerializerMethodField()    
    class Meta:
        model = api_models.Question_Answer_Message
        fields = '__all__'

    def get_profile(self, obj):
        user = obj.user

        if obj.is_teacher:
            teacher = api_models.Teacher.objects.filter(user=user).first()
            if teacher:
                return ProfileSerializer(teacher, context=self.context).data
        else:
            profile = Profile.objects.filter(user=user).first()
            if profile:
                return ProfileSerializer(profile, context=self.context).data

        return None
    

class QuestionAnswerSerializer(serializers.ModelSerializer):
    messages = QuestionAnswerMessagesSerializer(many=True)
    profile = ProfileSerializer(many=False)
    class Meta:
        model = api_models.Question_Answer
        fields = '__all__'


    

class CartOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.CartOrderItem
        fields = '__all__'
        # exclude = ('order',)
        depth = 1

class CartOrderSerializer(serializers.ModelSerializer):
    order_item = CartOrderItemSerializer(many=True)
    class Meta:
        model = api_models.CartOrder
        fields = '__all__'

class CertificateSerializer(serializers.ModelSerializer):

    class Meta:
        model = api_models.Certificate
        fields = '__all__'

class CompletedLessonSerializer(serializers.ModelSerializer):
    variant_item = VariantItemSerializer()
    class Meta:
        model = api_models.CompletedLesson
        fields = '__all__'


class NoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = api_models.Note
        fields = '__all__'
        extra_kwargs = {
            'user': {'read_only': True},
            'course': {'read_only' : True}
        }

class ReviewSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(many=False)
    user = UserSerializer()
    # course = serializers.CharField(source='course.course_id')
    class Meta:
        model = api_models.Review
        fields = '__all__'
        depth = 1

class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = api_models.Notification
        fields = '__all__'

class CouponSerializer(serializers.ModelSerializer):
    course = serializers.CharField(source='course.course_id')
    title = serializers.CharField(source='course.title')
    discount = serializers.IntegerField()
    class Meta:
        model = api_models.Coupon
        fields = '__all__'



class CountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = api_models.Country
        fields = '__all__'


class EnrolledCourseSerializer(serializers.ModelSerializer):
    lectures = VariantItemSerializer(many=True, read_only=True)
    completed_lessons = CompletedLessonSerializer(many=True, read_only=True)
    curriculem = VariantSerializer(many=True, read_only=True)
    note = NoteSerializer(many=True, read_only=True)
    question_answer = QuestionAnswerSerializer(many=True, read_only=True)
    review = ReviewSerializer(read_only=True)

    class Meta:
        model = api_models.EnrolledCourse
        # fields = '__all__'
        exclude = ('user',)
        depth = 1

class CourseSerializer(serializers.ModelSerializer):
    # students = EnrolledCourseSerializer(many=True)
    students = serializers.SerializerMethodField(read_only = True)
    curriculum = VariantSerializer(many=True, read_only=True)
    lectures = VariantItemSerializer(many=True, read_only=True)
    reviews =  ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = api_models.Course
        fields = [
            'course_id','slug','category','teacher','file','image','title','description','price','language','level','plateform_status','teacher_status','date', 'students','curriculum','lectures',"average_rating",'rating_count','reviews'
        ]
        depth = 1

    def get_students(self, obj):
        enrolled_users = obj.enrolledcourse_set.all().select_related('user')
        return [ec.user.id for ec in enrolled_users if ec.user]
    
   
class CartSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = api_models.Cart
        fields = '__all__'
        depth = 1
        

class StudentSummarySerializer(serializers.Serializer):
    total_courses = serializers.IntegerField(default = 0)
    completed_lessson = serializers.IntegerField(default=0)
    achived_certificates = serializers.IntegerField(default=0)

class TeacherSummarySerializer(serializers.Serializer):
    total_courses = serializers.IntegerField(default = 0)
    total_Students = serializers.IntegerField(default=0)
    total_revenue = serializers.IntegerField(default=0)
    monthly_revenue = serializers.IntegerField(default=0)

class WishlistCourseSerializer(serializers.ModelSerializer):
     class Meta:
        model = api_models.Course
        fields = [
            'course_id','slug','category','teacher','file','image','title','description','price','language','level','plateform_status','teacher_status','date', 'student_count',"average_rating",'rating_count'
        ]
        depth = 1

class WishlistSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    course = WishlistCourseSerializer()
    class Meta:
        model = api_models.Wishlist
        fields = '__all__'
        
class StudentEnrollmentIDSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source = 'user.id', read_only=True)
    course_id = serializers.CharField(source = 'course.course_id')

    class Meta:
        model = api_models.EnrolledCourse
        fields = ['user_id', 'course_id', 'enrollment_id']


class TeacherCourseIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Course
        fields = ['course_id', 'title', 'slug']