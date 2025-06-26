from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import NotFound

from decimal import Decimal
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.hashers import check_password
from django.db import models as db_models
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from datetime import timedelta
# from distutils.util import strtobool
from django.core.files.storage import default_storage

from . import serializers, models
from userauths.models import User, Profile
from utils.otp import generate_random_otp
from utils.emails import send_password_reset_email

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY
PAYPAL_CLIENT_ID = settings.PAYPAL_CLIENT_ID
PAYPAL_SECRET_ID = settings.PAYPAL_SECRET_ID

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = serializers.MyTokenObtainPairSerializer


# class RegisterGenericView(generics.CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = serializers.RegisterSerializer


class RegisterAPIView(APIView):
    def post(self, request):
        data = request.data
        serializer = serializers.RegisterSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message' : 'Register Successfully Done',
                'user': {
                    'full_name' : user.full_name,
                    'email' : user.email
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetEmailVerifyAPIView(APIView):
    def get(self, request, email):
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error' : 'This email is not exists with user'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            uuid64 = user.pk
            refresh_token = RefreshToken.for_user(user)
            access_token = str(refresh_token.access_token)

            user.otp = generate_random_otp()
            user.refresh_token = access_token
            user.save()
        except:
            return Response({'message': 'Some internal error occurrs'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        link = f'http://localhost:5173/create-new-password/?otp={user.otp}&uuid64={uuid64}&refresh_token={access_token}'

        send_password_reset_email(user, link)
        return Response({
            'message': 'successfully password reset link is sent to mail', 
            'link' : link
        }, status=status.HTTP_200_OK)
    
             
class PasswordResetAPIView(APIView):
    def post(self, request):
        data = request.data
        serializer = serializers.PasswordResetSerializer(data=data)
        if serializer.is_valid():
            otp = serializer.validated_data['otp']
            uuid64 = serializer.validated_data['uuid64']
            password = serializer.validated_data['password']

            user = User.objects.filter(id = uuid64, otp = otp).first()
            print(user)
            if not user:
               return Response({'error': 'Invalid OTP or UUID'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.otp = ''
            user.set_password(password)
            user.save()

            return Response({'message': 'Password Changed Successfully'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordAPIView(APIView):
    def post(self, request):
        serializer = serializers.ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            print(data)

            user = User.objects.filter(id = data['user_id']).first()

            if user is not None:
                if check_password(data['old_password'], user.password):
                    print(data['new_password'])
                    user.set_password(data['new_password'])
                    user.save()
                    return Response({'message' : 'Password changed successfully'}, status=status.HTTP_200_OK)
                return Response({'message' : 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'message' : 'User Not Found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        
class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.ProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        try:
            user_id = self.kwargs.get("user_id")
            profile =  Profile.objects.get(user__id=user_id)
        except:
            raise NotFound('Profile Not Found')
        return profile
        

class CategoryListAPIView(generics.ListAPIView):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer
    permission_classes = [AllowAny]

class CourseListAPIView(generics.ListAPIView):
    queryset = models.Course.objects.filter(plateform_status='Published', teacher_status="Published")
    serializer_class = serializers.CourseSerializer
    permission_classes = [AllowAny]

class CourseDetailAPIView(generics.RetrieveAPIView):
    queryset = models.Course.objects.filter(plateform_status='Published', teacher_status="Published")
    serializer_class = serializers.CourseSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

class CartAPIView(generics.CreateAPIView):
    queryset = models.Cart.objects.all()
    serializer_class = serializers.CartSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):

        required_fields = ['course_id', 'user_id', 'cart_id']
        missing_fields = [field for field in required_fields if not request.data.get(field)]

        if missing_fields:
            return Response({'error': f"Missing required fields: {', '.join(missing_fields)}"}, status=status.HTTP_400_BAD_REQUEST)

        course_id = request.data.get('course_id')
        user_id = request.data.get('user_id')
        # price = request.data.get('price')
        country_name = request.data.get('country_name')
        cart_id = request.data.get('cart_id')

        course = models.Course.objects.filter(course_id=course_id).first()
        if not course:
            return Response({'error': 'Invalid course_id'}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        if user_id and user_id != 'undefined':
            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response({'error': 'Invalid user_id'}, status=status.HTTP_400_BAD_REQUEST)
        # try:
        #     price = Decimal(price)
        # except:
        #     return Response({'error': 'Invalid price format'}, status=status.HTTP_400_BAD_REQUEST)
        
        country_obj = models.Country.objects.filter(name=country_name).first()
        if country_obj:
            tax_rate = country_obj.tax_rate / 100
            country = country_obj.name
        else:
            tax_rate = 0
            country = 'India'

        cart = models.Cart.objects.filter(cart_id=cart_id, course=course).first()
        created = False
        if not cart:
            cart = models.Cart()
            created = True

        cart.course = course
        cart.user = user
        cart.price = course.price
        cart.tax_fee = Decimal(course.price) * Decimal(tax_rate)
        cart.total = Decimal(course.price) + Decimal(cart.tax_fee)
        cart.country = country
        cart.cart_id = cart_id
        cart.save()

        return Response({
            'message': 'Cart Created Successfully' if created else 'Cart Updated Successfully',
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class LSMDetails(APIView):
    def get(self, request):
        course_count = models.Course.objects.all().count()
        enrolled_count = models.EnrolledCourse.objects.all().count()
        teacher_count = models.Teacher.objects.all().count()
        lectures_count = models.VariantItem.objects.all().count()

        data = {
            'course_count':course_count,
            'enrolled_count':enrolled_count,
            'teacher_count':teacher_count,
            'lecture_count':lectures_count
        }
        return Response(data, status=status.HTTP_200_OK)



class CartListAPIView(generics.ListAPIView):
    serializer_class = serializers.CartSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        cart_id = self.kwargs.get('cart_id')
        queryset = models.Cart.objects.filter(cart_id=cart_id)
        return queryset
        

class CartItemDeleteAPIView(generics.DestroyAPIView):
    queryset = models.Cart.objects.all()
    serializer_class = serializers.CartSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        cart_id = self.kwargs.get('cart_id')
        item_id = self.kwargs.get('item_id')

        try:
            obj = models.Cart.objects.get(cart_id=cart_id, course__course_id=item_id)
        except models.Cart.DoesNotExist:
            raise NotFound(detail="Cart item not found.")
        
        return obj


class CartStatsAPIView(generics.RetrieveAPIView):
    serializer_class = serializers.CartSerializer
    permission_classes = [AllowAny]
    lookup_field = 'cart_id' 

    def get_queryset(self):
        cart_id = self.kwargs.get('cart_id')
        queryset = models.Cart.objects.filter(cart_id=cart_id)
        return queryset
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        total_price = 0.00
        total_tax = 0.00
        total = 0.00

        for cart_item in queryset:
            total_price += float(cart_item.price)
            total_tax += float(cart_item.tax_fee)
            total += float(cart_item.total)

        data = {
            'total_price': total_price,
            'total_tax': total_tax,
            'total': total
        }

        return Response(data, status=status.HTTP_200_OK)
    

class CreateOrderAPIView(generics.CreateAPIView):
    queryset = models.CartOrder.objects.all()
    serializer_class = serializers.CartOrderSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        cart_id = request.data.get('cart_id')
        user_id = request.data.get('user_id')

        if not cart_id:
            return Response({'cart_id': 'This field is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if not user_id:
            return Response({'user_id': 'This field is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({'error': 'Invalid User ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item = models.Cart.objects.filter(cart_id=cart_id)

        total_price = Decimal(0.0)
        total_tax = Decimal(0.0)
        total_initial_price = Decimal(0.0)
        total= Decimal(0.0)

        if cart_item.first().user != user:
            return Response({'message': 'You Does not have access to This cart'}, status=status.HTTP_400_BAD_REQUEST)

        order = models.CartOrder.objects.create(
            full_name = user.full_name,
            email = user.email,
            country = cart_item.first().country,
            student = user,
            cart_id = cart_id
        )

        for c in cart_item:
            models.CartOrderItem.objects.create(
                order = order,
                course = c.course,
                price = c.price,
                tax_fee = c.tax_fee,
                total = c.total,
                initial_total= c.total,
                teacher= c.course.teacher
            )

            total_price += Decimal(c.price)
            total_tax += Decimal(c.tax_fee)
            total_initial_price += Decimal(c.total)
            total += Decimal(c.total)

            order.teacher.add(c.course.teacher)

        order.sub_total = total_price
        order.tax_fee = total_tax
        order.initial_total = total_initial_price
        order.total = total
        order.save()

        return Response({'message': 'Order Created successfully', 'order_oid' : order.oid},status=status.HTTP_201_CREATED)
    
class DeleteOrderAPIView(generics.DestroyAPIView):
    serializer_class = serializers.CartOrderSerializer
    permission_classes = [AllowAny]
    queryset = models.CartOrder.objects.all()
    lookup_field  = 'oid'

class CheckOutAPIView(generics.RetrieveAPIView):
    queryset = models.CartOrder.objects.all()
    serializer_class = serializers.CartOrderSerializer
    permission_classes = [AllowAny]
    lookup_field = 'oid'

class CouponApplyAPIView(generics.CreateAPIView):
    serializer_class = serializers.CouponSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')
        coupon_code = request.data.get('coupon_code')

        if not order_id or not coupon_code:
            return Response({'error': 'Order ID and Coupon Code are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate Order
        order = models.CartOrder.objects.filter(oid=order_id).first()
        if not order:
            return Response({'error': 'Order does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate Coupon
        coupon = models.Coupon.objects.filter(code=coupon_code).first()
        if not coupon:
            return Response({'error': 'Coupon does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Apply Coupon to Matching Course in Order
        order_items = models.CartOrderItem.objects.filter(order=order)
        applied = False
        
        for item in order_items:
            if item.course == coupon.course:
                if item.applied_coupon:
                    return Response({'message': 'Already One Coupon is Applied'}, status=status.HTTP_400_BAD_REQUEST)
                
                item.coupons = coupon
                item.applied_coupon = True
                item.saved = coupon.discount
                item.total = Decimal(item.total) - Decimal(coupon.discount)
                item.save()

                order.coupons.add(coupon)
                order.saved += coupon.discount
                order.total = Decimal(order.total) - Decimal(coupon.discount)
                order.save()

                applied = True
                break

        if not applied:
            return Response({'message': 'No matching course found for coupon'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Coupon applied successfully'}, status=status.HTTP_200_OK)

        

class SearchCourseAPIView(generics.ListAPIView):
    serializer_class = serializers.CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = self.request.GET.get('query')
        return models.Course.objects.filter(title__icontains = query)




class StripeCheckoutAPIView(generics.CreateAPIView):
    serializer_class = serializers.CartOrderSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):

        order_oid = self.kwargs.get('order_oid')
        order = models.CartOrder.objects.filter(oid=order_oid).first()

        if not order:
            return Response({'message': 'Order Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email = order.email,
                payment_method_types = ['card'],
                line_items = [
                    {
                        'price_data' : {
                            'currency':'inr',
                            'product_data' : {
                                'name':order.full_name,
                            },
                            'unit_amount' : int(order.total) * 100
                        },
                        'quantity' : 1
                    }  
                ],
                mode = 'payment',
                success_url = settings.FRONTEND_SITE_URL + 'payment-success/' + f'{order.oid}' + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url = settings.FRONTEND_SITE_URL + 'payment-failed/'
            )
            order.stripe_session_id = checkout_session.id
            order.save()
            print(checkout_session)
            return redirect(checkout_session.url)
        except Exception as e:
            return Response({'message': 'Something went wrong ', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    
class PaymentSuccessAPIView(generics.CreateAPIView):
    serializer_class = serializers.CartOrderSerializer
    queryset = models.CartOrder.objects.all()

    def create(self, request, *args, **kwargs):
        order_oid = request.data.get('order_oid')
        session_id = request.data.get('session_id')

        order = models.CartOrder.objects.filter(oid=order_oid).first()
        if not order:
            return Response({'message': 'Order Not Found'}, status=status.HTTP_400_BAD_REQUEST)

        if order.payment_status == 'Paid':
            return Response({'message': 'Already Paid'}, status=status.HTTP_200_OK)

        if session_id is None:
            return Response({'message': 'Please Provide Session or Paypal ID'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve Stripe session
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status != 'paid':
            return Response({'message': 'Payment Failed'}, status=status.HTTP_400_BAD_REQUEST)

        # Payment is valid and was not processed before
        order.payment_status = 'Paid'
        order.save()

        models.Notification.objects.get_or_create(
            user=order.student,
            order=order,
            type='Course Enrollment Completed'
        )

        order_items = models.CartOrderItem.objects.filter(order=order)
        for o in order_items:
            models.Notification.objects.get_or_create(
                teacher=o.teacher,
                order=order,
                order_item=o,
                type='New Order'
            )
            models.EnrolledCourse.objects.get_or_create(
                course=o.course,
                user=order.student,
                teacher=o.teacher,
                order_item=o
            )

        # Clear cart
        models.Cart.objects.filter(cart_id=order.cart_id).delete()
        order.cart_id = None
        order.save()

        return Response({'message': 'Payment successfull'}, status=status.HTTP_200_OK)


class StudentSummaryAPIView(generics.ListAPIView):
    serializer_class = serializers.StudentSummarySerializer
    permission_classes = [AllowAny]

    
    def list(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')

        if not user_id:
            return Response({'message' : 'User Id not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(id = user_id).first()

        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        total_courses = user.enroll_courses.all().count()
        completed_lessons = models.CompletedLesson.objects.filter(user=user).count()
        achived_certificate = models.Certificate.objects.filter(user = user).count()

        data = {
            'total_courses': total_courses,
            'completed_lessons' : completed_lessons,
            'achived_certificate' : achived_certificate
        }

        return Response(data, status=status.HTTP_200_OK)


class StudentCourseListAPIView(generics.ListAPIView):
    serializer_class = serializers.EnrolledCourseSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        queryset = models.EnrolledCourse.objects.filter(user__id=user_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        
class StudentEnrollmentAndCourseIDAPIView(generics.ListAPIView):
    serializer_class = serializers.StudentEnrollmentIDSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return models.EnrolledCourse.objects.filter(user__id=user_id) 
        


class StudentCourseDetailsAPIView(generics.RetrieveAPIView):
    serializer_class = serializers.EnrolledCourseSerializer
    permission_classes = [AllowAny]
    queryset = models.EnrolledCourse.objects.all()
    lookup_field = 'enrollment_id'


class StudentCourseCompletedAPIView(generics.CreateAPIView):
    serializer_class = serializers.CompletedLessonSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        course_id = request.data.get('course_id')
        variant_item_id = request.data.get('variant_item_id')

        if not user_id:
            return Response({'message' : 'user id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not course_id:
            return Response({'message' : 'course id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not variant_item_id:
            return Response({'message' : 'variant_item_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(id = user_id).first()

        if not user:
            return Response({'message': 'User Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        course = models.Course.objects.filter(course_id = course_id).first()

        if not course:
            return Response({'message': 'Course Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        variant_item = models.VariantItem.objects.filter(variant_item_id = variant_item_id).first()
        
        if not variant_item:
            return Response({'message': 'Variant Item Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        completed_lesson = models.CompletedLesson.objects.filter(user=user, course=course, variant_item=variant_item).first()

        if completed_lesson:
            completed_lesson.delete()
            return Response({'message': 'Course marked as not completed'}, status=status.HTTP_200_OK)
        
        enrolled = models.EnrolledCourse.objects.filter(user=user, course=course).exists()

        if not enrolled:
            return Response({'message' : 'This user not enrolled this course'}, status=status.HTTP_400_BAD_REQUEST)
        
        models.CompletedLesson.objects.create(user=user, course=course, variant_item=variant_item)
        return Response({'message' : 'Course marked as completed'}, status=status.HTTP_200_OK)
    

        
class StudentWishlistAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.WishlistSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        wishlists = models.Wishlist.objects.filter(user__id = user_id)
        serializer = self.get_serializer(wishlists, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        course_id = request.data.get('course_id')

        if not user_id:
            return Response({'message' : 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not course_id:
            return Response({'message' : 'course_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(id = user_id).first()
        if not user:
            return Response({'message': 'User Not Found'}, status=status.HTTP_404_NOT_FOUND)  
        course = models.Course.objects.filter(course_id = course_id).first()
        if not course:
            return Response({'message': 'Course Not Found'}, status=status.HTTP_404_NOT_FOUND)  
            
        wishlist, created = models.Wishlist.objects.get_or_create(user = user, course = course)
        if not created:
            wishlist.delete()
            return Response({'message' : 'Course remove from wishlist successfully'}, status=status.HTTP_200_OK)

        return Response({'message' : 'Course added in wishlist successfully'}, status=status.HTTP_200_OK)
    

class StudentNoteCreateAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.NoteSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        enrollment_id = request.data.get('enrollment_id')

        if not enrollment_id:
            return Response({'message' : 'enrollment_id is required'}, status=status.HTTP_200_OK)
        
        enrolled = models.EnrolledCourse.objects.filter(enrollment_id = enrollment_id).first()

        if not enrolled:
            return Response({'message' : 'Enrollment id is wrong'}, status=status.HTTP_400_BAD_REQUEST)
        
        notes = models.Note.objects.filter(user = enrolled.user, course = enrolled.course)
        serializer = self.get_serializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

        

    def create(self, request, *args, **kwargs):
        enrollment_id = request.data.get('enrollment_id')
        title = request.data.get('title')
        note = request.data.get('note')

        if not enrollment_id:
            return Response({'message' : 'enrollment_id is required'}, status=status.HTTP_200_OK)
        if not title:
            return Response({'message' : 'title is required'}, status=status.HTTP_200_OK)
        if not note:
            return Response({'message' : 'note is required'}, status=status.HTTP_200_OK)


        enrolled = models.EnrolledCourse.objects.filter(enrollment_id = enrollment_id).first()

        if not enrolled:
            return Response({'message' : 'Enrollment id is wrong'}, status=status.HTTP_400_BAD_REQUEST)
        
        note = models.Note.objects.create(user = enrolled.user, course = enrolled.course, title = title, note = note)

        return Response({'message' : 'Note created successfully', 'note_id' : note.note_id}, status=status.HTTP_200_OK)
    

class StudentNoteDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.NoteSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        note_id = self.kwargs.get('note_id')
        try:
            note = models.Note.objects.get(user__id = user_id, note_id = note_id)
        except:
            raise NotFound(detail="Note not found.")
        return note
    

    
    
    

class StudentRateCourseCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.ReviewSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        course_id = request.data.get('course_id')
        rating = request.data.get('rating')
        review = request.data.get('review')
        rows = [user_id, course_id, rating,review]
        field_names = ['user_id', 'course_id', 'rating', 'review']
        
        for i, data in enumerate(rows):
            if not data:
                return Response({'message' : f'{field_names[i]} is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.filter(id = user_id).first()
        if not user:
            return Response({'message' : 'User Not Found'}, status=status.HTTP_400_BAD_REQUEST)
        
        course = models.Course.objects.filter(course_id = course_id).first()
        if not course:
            return Response({'message' : 'Course Not Found'}, status=status.HTTP_400_BAD_REQUEST)
        
        enrolled = models.EnrolledCourse.objects.filter(user=user, course = course).exists()
        if not enrolled:
            return Response({'message': 'User Does Not Enrolled This Course'}, status=status.HTTP_400_BAD_REQUEST)
        
        models.Review.objects.create(
            user=user,
            course=course,
            review=review,
            rating=rating
        )

        return Response({'message' : 'Review Created Successdully'}, status=status.HTTP_200_OK)
    
        

class StudentRateCourseUpdateAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.ReviewSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        review_id = self.kwargs.get('review_id')

        try:
            review = models.Review.objects.get(user__id = user_id, id = review_id)
        except:
            raise NotFound('Review Not Found')
        return review

    def partial_update(self, request, *args, **kwargs):
        rating = request.data.get('rating')
        review = request.data.get('review')

        obj = self.get_object()
        obj.rating = rating
        obj.review = review
        obj.save()
        
        serializer = self.get_serializer(obj, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
        

    

    
class QuestionAnswerListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.QuestionAnswerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        course_id = self.request.data.get('course_id')
        return models.Question_Answer.objects.filter(course__course_id = course_id)
    
    def create(self, request, *args, **kwargs):
        course_id = request.data.get('course_id')
        user_id = request.data.get('user_id')
        title = request.data.get('title')
        message = request.data.get('message')

        if not course_id:
            return Response({'message' : 'course_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not user_id:
            return Response({'message' : 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not title:
            return Response({'message' : 'title is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not message:
            return Response({'message' : 'message is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({'message' : 'User Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        course = models.Course.objects.filter(course_id = course_id).first()
        if not course:
            return Response({'message' : 'Course Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        question = models.Question_Answer.objects.create(
            course=course,
            user=user,
            title=title
        )

        models.Question_Answer_Message.objects.create(
            course=course,
            user=user,
            message=message,
            question=question 
        )

        return Response({'message': 'Question is created successfully'}, status=status.HTTP_200_OK)
    
        

class QuestionAnswerMessageSendAPIView(generics.CreateAPIView):
    serializer_class = serializers.QuestionAnswerSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        teacher_id = request.GET.get('teacher_id')
        qa_id = request.data.get('qa_id')
        user_id = request.data.get('user_id')
        message = request.data.get('message')

        if not qa_id:
            return Response({'message' : 'qa_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not user_id:
            return Response({'message' : 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not message:
            return Response({'message' : 'message is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({'message': 'User Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        question = models.Question_Answer.objects.filter(qa_id=qa_id).first()
        if not question:
            return Response({'message':'Question Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        is_teacher = False
        if teacher_id:
            is_teacher = True
            print(is_teacher)
        models.Question_Answer_Message.objects.create(
            question=question,
            user=user,
            course=question.course,
            message=message,
            is_teacher = is_teacher
        )


        serializer = self.get_serializer(question, many=False)

        return Response({'message' : 'Question And Answer created successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
    
class TeacherDetailsAPIView(generics.RetrieveUpdateAPIView):
    queryset = models.Teacher.objects.all()
    serializer_class = serializers.TeacherSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

class TeacherSummaryAPIView(generics.ListAPIView):
    serializer_class = serializers.TeacherSummarySerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        teacher_id = self.kwargs.get('teacher_id')

        teacher = models.Teacher.objects.filter(id=teacher_id).first()
        if not teacher:
            return Response({'message' : 'Teacher Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        one_month_ago = timezone.now() - timedelta(days=28)

        total_courses = teacher.courses().count()
        total_revenue = teacher.students().aggregate(total_revenue=db_models.Sum('price'))['total_revenue'] or 0
        monthly_revenue = teacher.students().filter(date__gt=one_month_ago).aggregate(total_revenue=db_models.Sum('price'))['total_revenue'] or 0
        
        enrolled_courses = models.EnrolledCourse.objects.filter(teacher = teacher).select_related('user')
        unique_student_ids = set()
        # students = []

        for course in enrolled_courses:
            if course.user.id not in unique_student_ids:
                # user = User.objects.filter(id=course.user.id).first()
                # student = {
                #     'full_name':user.profile.full_name,
                #     'image': user.profile.image,
                #     'country': user.profile.country,
                #     'date': course.date
                # }

                # students.append(student)
                unique_student_ids.add(course.user.id)

        return Response({
            'total_courses': total_courses,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'total_students': len(unique_student_ids)
        }, status=status.HTTP_200_OK)
        

class TeacherCourseListAPIView(generics.ListAPIView):
    serializer_class = serializers.CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs.get('teacher_id')
        return models.Course.objects.filter(teacher__id = teacher_id)
    

class TeacherReviewListAPIView(generics.ListAPIView):
    serializer_class = serializers.ReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs.get('teacher_id')
        return models.Review.objects.filter(course__teacher__id = teacher_id)
    

class TeacherReviewDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.ReviewSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        teacher_id = self.kwargs.get('teacher_id')
        review_id = self.kwargs.get('review_id')
        try:
            review = models.Review.objects.get(course__teacher__id = teacher_id, id=review_id)
        except:
            raise NotFound('Review Not Found')
        return review
    

class TeacherStudentsListAPIView(viewsets.ViewSet):
    def list(self, request, teacher_id = None):
        teacher = models.Teacher.objects.filter(id=teacher_id).first()
        if not teacher:
            return Response({'message': 'Teacher Not Found'})
        enrolled_courses = models.EnrolledCourse.objects.filter(teacher = teacher).select_related('user')
        unique_student_ids = set()
        students = []

        for course in enrolled_courses:
            print(course)
            if course.user.id not in unique_student_ids:
                user = course.user
                student = {
                    'id': user.id,
                    'course': course.course.title,
                    'full_name':user.profile.full_name,
                    'image': user.profile.image.url,
                    'country': user.profile.country,
                    'date': course.date
                }

                students.append(student)
                unique_student_ids.add(course.user.id)

        return Response(students, status=status.HTTP_200_OK)
    
        
class TeacherAllMonthEarningAPIView(APIView):
    def get(self, request, teacher_id):
        teacher = models.Teacher.objects.filter(id=teacher_id).first()
        if not teacher:
            return Response({'message': 'Teacher not found'}, status=status.HTTP_404_NOT_FOUND)
        
        monthly_earning_teacher = (
            teacher.students()
            .annotate(
                month=ExtractMonth('date')
            )
            .values('month')
            .annotate(
                total_earning = db_models.Sum('price')
            )
            .order_by('month')
        )

        return Response( monthly_earning_teacher, status=status.HTTP_200_OK)


class TeacherBestSellingCourseAPIView(generics.ListAPIView):
    serializer_class = serializers.CourseSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        teacher_id = self.kwargs.get('teacher_id')
        teacher = models.Teacher.objects.filter(id=teacher_id).first()

        if not teacher:
            return Response({'message': 'Teacher Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        courses_with_total_price = []
        courses = teacher.courses()

        for course in courses:
            enroll = course.enrolledcourse_set
            revenue = enroll.all().aggregate(total_price=db_models.Sum('order_item__price'))['total_price'] or 0
            sales = enroll.all().count()

            courses_with_total_price.append({
                'course_id': course.course_id,
                'slug': course.slug, 
                'course_image':course.image.url,
                'course_title': course.title,
                'revenue': revenue,
                'sales': sales
            })
        courses_with_total_price = sorted(courses_with_total_price, key=lambda x: x['sales'], reverse=True)
        return Response(courses_with_total_price, status=status.HTTP_200_OK) 


class TeacherCourseOrderListAPIView(generics.ListAPIView):
    serializer_class =  serializers.CartOrderItemSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        teacher_id = self.kwargs.get('teacher_id')
        teacher = models.Teacher.objects.filter(id=teacher_id).first()
        if not teacher:
            return Response({'message': 'Teacher Not Found'}, status=status.HTTP_404_NOT_FOUND)
        cot = models.CartOrderItem.objects.filter(teacher=teacher)

        serializer = self.get_serializer(cot, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class TeacherQuestionAnswerListAPIView(generics.ListAPIView):
    serializer_class = serializers.QuestionAnswerSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        teacher_id = self.kwargs.get('teacher_id')
        teacher = models.Teacher.objects.filter(id=teacher_id).first()
        if not teacher:
            return Response({'message': 'Teacher Not Found'}, status=status.HTTP_404_NOT_FOUND)
        qa = models.Question_Answer.objects.filter(course__teacher=teacher)

        serializer = self.get_serializer(qa, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    

class TeacherCouponListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.CouponSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs.get('teacher_id')
        return models.Coupon.objects.filter(course__teacher__id = teacher_id)
    
    def create(self, request, *args, **kwargs):
        teacher_id = self.kwargs.get('teacher_id')
        code = request.data.get('code')
        course_id = request.data.get('course')
        discount = request.data.get('discount')

        if not code:
            return Response({'message': 'code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not course_id:
            return Response({'message': 'course is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not discount:
            return Response({'message': 'discount is required'}, status=status.HTTP_400_BAD_REQUEST)

        course = models.Course.objects.filter(course_id=course_id).first()

        if not course:
            return Response({'message': 'Course Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not course.teacher.id == int(teacher_id):
            return Response({'message' : 'Course not own by this teacher'}, status=status.HTTP_400_BAD_REQUEST)
        
        if int(discount) < 1:
            return Response({'message' : ' Discount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
        
        coupon = models.Coupon.objects.create(
            course=course,
            code=code,
            discount=int(discount)
        )
        serializer = self.get_serializer(coupon, many=False)

        return Response(serializer.data, status=status.HTTP_200_OK)
      
        
class TeacherCouponDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.CouponSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        teacher_id = self.kwargs.get('teacher_id')
        coupon_id = self.kwargs.get('coupon_id')

        coupon = models.Coupon.objects.filter(course__teacher__id = teacher_id, id = coupon_id).first()
        if not coupon:
            raise NotFound('Coupon Not Found')
        return coupon
    
    def partial_update(self, request, *args, **kwargs):
        teacher_id = self.kwargs.get('teacher_id')
        coupon_id = self.kwargs.get('coupon_id')

        coupon = models.Coupon.objects.filter(id=coupon_id).first()

        if not coupon:
            return Response({'message': 'Coupon not found'}, status=status.HTTP_404_NOT_FOUND)

        course = coupon.course  # Default to existing course

        course_id = request.data.get('course')
        if course_id:
            course = models.Course.objects.filter(course_id=course_id).first()
            if not course:
                return Response({'message': 'Course Not Found'}, status=status.HTTP_404_NOT_FOUND)
            if course.teacher.id != int(teacher_id):
                return Response({'message': 'Course not owned by this teacher'}, status=status.HTTP_400_BAD_REQUEST)

        if 'discount' in request.data:
            discount = int(request.data.get('discount'))
            if discount < 1:
                return Response({'message': 'Discount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            coupon.discount = discount

        if 'code' in request.data:
            coupon.code = request.data.get('code')

        coupon.course = course
        coupon.save()

        serializer = self.get_serializer(coupon, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        teacher_id = self.kwargs.get('teacher_id')
        coupon_id = self.kwargs.get('coupon_id')  # assuming you're using pk to identify coupon

        code = request.data.get('code')
        course_id = request.data.get('course')
        discount = request.data.get('discount')

        if not code:
            return Response({'message': 'code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not course_id:
            return Response({'message': 'course is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not discount:
            return Response({'message': 'discount is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        course = models.Course.objects.filter(course_id=course_id).first()

        if not course:
            return Response({'message': 'Course Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        if course.teacher.id != int(teacher_id):
            return Response({'message': 'Course not owned by this teacher'}, status=status.HTTP_400_BAD_REQUEST)
        
        if int(discount) < 1:
            return Response({'message': 'Discount must be positive'}, status=status.HTTP_400_BAD_REQUEST)

        coupon = models.Coupon.objects.filter(id=coupon_id).first()

        if not coupon:
            return Response({'message': 'Coupon not found'}, status=status.HTTP_404_NOT_FOUND)

        coupon.course = course
        coupon.code = code
        coupon.discount = int(discount)
        coupon.save()

        serializer = self.get_serializer(coupon, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TeacherCourseWithCourseIdAPIView(generics.ListAPIView):
    serializer_class = serializers.TeacherCourseIDSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs.get('teacher_id')
        return models.Course.objects.filter(teacher__id = teacher_id)

class TeacherNotificationListAPIView(generics.ListAPIView):
    serializer_class = serializers.NotificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs.get('teacher_id')
        return models.Notification.objects.filter(teacher__id = teacher_id, seen=False)
    
class TeacherNotificationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.NotificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs.get('teacher_id')
        notification_id = self.kwargs.get('notification_id')
        return models.Notification.objects.filter(teacher__id = teacher_id,id=notification_id)
    
    def get_object(self):
        queryset = self.get_queryset().first()
        if not queryset:
            raise NotFound('Notifiaction Not Found')
        return queryset
    
# class CourseCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CourseSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        course_instance = serializer.save()

        variant_datas = []

        for key, value in self.request.data.items():
            if key.startswith('variant') and '[variant_title]' in key:
                index = key.split('[')[1].split(']')[0]
                title = value

                variant_data = {'title': title}
                item_data_list = []
                current_item = {}

                for item_key, item_value in self.request.data.items():
                    if f'variants[{index}][items]' in item_key:
                        field_name = item_key.split('[')[-1].split(']')[0]
                        if field_name == 'title':
                            if current_item:
                                item_data_list.append(current_item)
                            current_item = {}
                        current_item.update({field_name: item_value})
                if current_item:
                    item_data_list.append(current_item)

                variant_datas.append({
                    'variant_data': variant_data,
                    'variant_item_data': item_data_list
                })

        for data_entry in variant_datas:
            variant = models.Variant.objects.create(
                title=data_entry['variant_data']['title'],
                course=course_instance
            )

            for item_data in data_entry['variant_item_data']:
                preview_value = item_data.get('preview')
                preview = bool(strtobool(str(preview_value))) if preview_value is not None else False

                models.VariantItem.objects.create(
                    variant=variant,
                    title=item_data.get('title'),
                    description=item_data.get('description'),
                    file=item_data.get('file'),
                    preview=preview
                )

    # Optional cleanup method if you plan to use DRF serializers for nested data
    def save_nested_data(self, course_instance, serializer_class, data):
        serializer = serializer_class(data=data, many=True, context={'course_instance': course_instance})
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course_instance)

class CourseCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.CourseSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        teacher_id = self.kwargs.get('teacher_id')
        title = request.data.get('title')
        description = request.data.get('description')
        image = request.FILES.get('image')
        file = request.FILES.get('file')
        level = request.data.get('level')
        language = request.data.get('language')
        price = request.data.get('price')
        category = request.data.get('category')
        teacher_status = request.data.get('teacher_status')

        print(request.FILES)

        if not title:
            return Response({'message': 'title is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not description:
            return Response({'message': 'description is required'}, status=status.HTTP_400_BAD_REQUEST)
        print('IMAGE', image)
        if not image:
            return Response({'message': 'image is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not price:
            return Response({'message': 'price is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not category:
            return Response({'message': 'category is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not file:
            return Response({'message': 'file is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not level:
            return Response({'message': 'level is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not language:
            return Response({'message': 'language is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not teacher_status:
            return Response({'message': 'teacher_status is required'}, status=status.HTTP_400_BAD_REQUEST)
        

        teacher = models.Teacher.objects.filter(id=teacher_id).first()
        if not teacher:
            return Response({'message' : 'Teacher Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        category = models.Category.objects.filter(slug=category).first()
        if not category:
            return Response({'message': 'Category Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        course = models.Course.objects.create(
            teacher=teacher,
            title=title,
            category=category,
            price=price,
            level=level,
            language=language,
            file=file,
            image=image,
            description=description,
            teacher_status=teacher_status
        )
        
        return Response({'message' : 'course created successfully', 'course_id': course.course_id}, status=status.HTTP_201_CREATED)


from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from . import models, serializers


class TeacherCourseDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.CourseSerializer
    permission_classes = [AllowAny]
    queryset = models.Course.objects.all()
    lookup_field = 'course_id'

    def partial_update(self, request, *args, **kwargs):
        teacher_id = self.kwargs.get('teacher_id')
        course_id = self.kwargs.get('course_id')

        course = models.Course.objects.filter(course_id=course_id, teacher__id=teacher_id).first()
        if not course:
            return Response({'message': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        # Extract data from request
        title = request.data.get('title', course.title)
        description = request.data.get('description', course.description)
        level = request.data.get('level', course.level)
        language = request.data.get('language', course.language)
        price = request.data.get('price', course.price)
        teacher_status = request.data.get('teacher_status', course.teacher_status)

        image = request.FILES.get('image', None)
        file = request.FILES.get('file', None)

        category_id = request.data.get('category')
        category = course.category
        if category_id:
            category = models.Category.objects.filter(slug=category_id).first()
            if not category:
                return Response({'message': 'Invalid category'}, status=status.HTTP_400_BAD_REQUEST)

        # Update fields
        course.title = title
        course.description = description
        course.level = level
        course.language = language
        course.price = price
        course.teacher_status = teacher_status
        course.category = category

        if image:
            course.image = image
        if file:
            course.file = file

        course.save()

        return Response({'message': 'Course updated successfully'}, status=status.HTTP_200_OK)

class TeacherCourseDeleteAPIView(generics.DestroyAPIView):
    serializer_class = serializers.CourseSerializer
    permission_classes = [AllowAny]
    queryset = models.Course.objects.all()
    lookup_field = 'course_id'
        
class CourseVariantCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.VariantSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        teacher_id = self.kwargs.get('teacher_id')
        course_id = self.kwargs.get('course_id')
        title = request.data.get('title')

        if not title:
            return Response({'message': 'title is required'}, status=status.HTTP_400_BAD_REQUEST)

        course = models.Course.objects.filter(teacher__id=teacher_id, course_id=course_id).first()
        if not course:
            return Response({'message': 'Course Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        variant = models.Variant.objects.create(course=course, title=title)
        serializer = self.get_serializer(variant, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CourseVariantDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.VariantSerializer
    permission_classes = [AllowAny]
    queryset = models.Variant.objects.all()
    lookup_field = 'variant_id'


class CourseVariantItemCreateAPIView(generics.CreateAPIView):
    serializer_class = serializers.VariantItemSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        teacher_id = self.kwargs.get('teacher_id')
        course_id = self.kwargs.get('course_id')
        variant_id = self.kwargs.get('variant_id')
        title = request.data.get('title')

        if not title:
            return Response({'message': 'title is required'}, status=status.HTTP_400_BAD_REQUEST)

        variant = models.Variant.objects.filter(variant_id=variant_id).first()
        if not variant:
            return Response({'message': 'Variant Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        var_item = models.VariantItem.objects.create(variant=variant, title=title)
        serializer = self.get_serializer(var_item, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CourseVariantItemDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.VariantItemSerializer
    permission_classes = [AllowAny]
    queryset = models.VariantItem.objects.all()
    lookup_field = 'variant_item_id'
        




                
    

            
        
        
            
        





