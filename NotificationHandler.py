import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
from typing import List, Dict, Optional
import logging



class NotificationHandler:
    """
    Simple email notification handler for sending emails with text content,
    URL links, and image attachments.
    """

    def __init__(self, email: str, password: str, provider: str = 'gmail'):
        """
        Initialize the email handler.
        Args:
            email: Your email address
            password: Your email password (use app password for Gmail)
            provider: Email provider ('gmail', 'outlook', 'yahoo')
        """
        self.sender_email = email
        self.password = password

        # SMTP configurations for different providers
        smtp_configs = {
            'gmail': {'server': 'smtp.gmail.com', 'port': 587},
            'outlook': {'server': 'smtp-mail.outlook.com', 'port': 587},
            'yahoo': {'server': 'smtp.mail.yahoo.com', 'port': 587}
        }

        if provider.lower() not in smtp_configs:
            raise ValueError(f"Unsupported provider: {provider}")

        config = smtp_configs[provider.lower()]
        self.smtp_server = config['server']
        self.smtp_port = config['port']

        # Setup basic logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('EmailHandler')

    def create_email_content(self,
                             text_content: str,
                             urls: Optional[List[Dict[str, str]]] = None,
                             images: Optional[List[str]] = None) -> str:
        """
        Create HTML email content with text, URLs, and images.

        Args:
            text_content: Main text content of the email
            urls: List of dicts with 'url' and 'text' keys for clickable links
            images: List of image file paths to embed in email

        Returns:
            HTML content string
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .url-section {{ margin: 20px 0; }}
                .url-link {{ display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 5px 0; }}
                .url-link:hover {{ background: #0056b3; }}
                .image-section {{ text-align: center; margin: 20px 0; }}
                .email-image {{ max-width: 100%; height: auto; border-radius: 5px; margin: 10px; }}
            </style>
        </head>
        <body>
            <div class="content">
                <div class="text-content">
                    {text_content.replace(chr(10), '<br>')}
                </div>
        """

        # Add URLs section
        if urls:
            html_content += '<div class="url-section"><h3>Links:</h3>'
            for url_item in urls:
                url = url_item.get('url', '')
                text = url_item.get('text', url)
                html_content += f'<a href="{url}" class="url-link" target="_blank">{text}</a><br>'
            html_content += '</div>'

        # Add images section
        if images:
            html_content += '<div class="image-section"><h3>Images:</h3>'
            for i, image_path in enumerate(images):
                if os.path.exists(image_path):
                    html_content += f'<img src="cid:image_{i}" class="email-image" alt="Attached Image {i + 1}"><br>'
            html_content += '</div>'

        html_content += """
            </div>
        </body>
        </html>
        """

        return html_content

    def send_email(self,
                   recipients: List[str],
                   subject: str,
                   text_content: str,
                   urls: Optional[List[Dict[str, str]]] = None,
                   images: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Send email to multiple recipients with text, URLs, and images.

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            text_content: Main text content
            urls: List of dicts with 'url' and 'text' keys
                  Example: [{'url': 'https://google.com', 'text': 'Visit Google'}]
            images: List of image file paths to attach
                   Example: ['photo1.jpg', 'logo.png']

        Returns:
            Dict mapping email addresses to success status (True/False)
        """
        results = {}

        try:
            # Create SSL context
            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.password)

                for recipient in recipients:
                    try:
                        # Create message
                        message = MIMEMultipart('related')
                        message['From'] = self.sender_email
                        message['To'] = recipient
                        message['Subject'] = subject

                        # Create HTML content
                        html_content = self.create_email_content(text_content, urls, images)

                        # Add HTML part
                        html_part = MIMEText(html_content, 'html')
                        message.attach(html_part)

                        # Add images as embedded attachments
                        if images:
                            for i, image_path in enumerate(images):
                                if os.path.exists(image_path):
                                    with open(image_path, 'rb') as img_file:
                                        img_data = img_file.read()
                                        image = MIMEImage(img_data)
                                        image.add_header('Content-ID', f'<image_{i}>')
                                        image.add_header('Content-Disposition',
                                                         f'inline; filename="{os.path.basename(image_path)}"')
                                        message.attach(image)
                                else:
                                    self.logger.warning(f"Image not found: {image_path}")

                        # Send email
                        server.send_message(message)
                        results[recipient] = True
                        self.logger.info(f"Email sent successfully to {recipient}")

                    except Exception as e:
                        results[recipient] = False
                        self.logger.error(f"Failed to send email to {recipient}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Failed to connect to SMTP server: {str(e)}")
            for recipient in recipients:
                results[recipient] = False

        return results
