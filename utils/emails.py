from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_password_reset_email(user, reset_link):
    """
    Sends password reset email to the user with HTML template.
    """
    subject = 'Password Reset Link'
    to_email = user.email
    text_content = f"Hi {user.username},\n\nUse this link to reset your password:\n{reset_link}"

    html_content = render_to_string('email/password_reset.html', {
        'username': user.username,
        'link': reset_link,
    })

    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send()
