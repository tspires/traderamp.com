"""
AWS Lambda function to handle form submissions from TradeRamp website
Deploy this with API Gateway for the /api/schedule-call endpoint
"""

import json
import boto3
import os
from datetime import datetime
from urllib.parse import parse_qs

# Initialize AWS services
ses = boto3.client('ses', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb')

# Environment variables
NOTIFICATION_EMAIL = os.environ.get('NOTIFICATION_EMAIL', 'leads@traderamp.com')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@traderamp.com')
TABLE_NAME = os.environ.get('TABLE_NAME', 'traderamp-leads')

def lambda_handler(event, context):
    """Handle form submission"""
    
    try:
        # Parse form data
        if event.get('body'):
            # Handle both JSON and form-encoded data
            content_type = event.get('headers', {}).get('content-type', '')
            
            if 'application/json' in content_type:
                form_data = json.loads(event['body'])
            else:
                # Parse URL-encoded form data
                parsed = parse_qs(event['body'])
                form_data = {k: v[0] for k, v in parsed.items()}
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'No form data received'})
            }
        
        # Extract form fields
        contact_name = form_data.get('contact-name', '')
        business_name = form_data.get('business-name', '')
        email = form_data.get('contact-email', '')
        phone = form_data.get('contact-phone', '')
        trade_type = form_data.get('trade-type', '')
        message = form_data.get('contact-message', '')
        
        # Validate required fields
        if not all([contact_name, business_name, email, phone, trade_type]):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Missing required fields'})
            }
        
        # Save to DynamoDB (optional)
        if TABLE_NAME:
            try:
                table = dynamodb.Table(TABLE_NAME)
                table.put_item(
                    Item={
                        'id': f"{datetime.utcnow().isoformat()}_{email}",
                        'timestamp': datetime.utcnow().isoformat(),
                        'contact_name': contact_name,
                        'business_name': business_name,
                        'email': email,
                        'phone': phone,
                        'trade_type': trade_type,
                        'message': message,
                        'source': 'website-form'
                    }
                )
            except Exception as e:
                print(f"DynamoDB error: {str(e)}")
                # Continue even if DB save fails
        
        # Prepare email
        email_subject = f"New Lead: {business_name} - {trade_type}"
        email_body = f"""
New lead from TradeRamp website:

Contact Name: {contact_name}
Business Name: {business_name}
Email: {email}
Phone: {phone}
Trade Type: {trade_type}

Message:
{message or 'No message provided'}

---
Submitted at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        # Send notification email
        ses.send_email(
            Source=FROM_EMAIL,
            Destination={'ToAddresses': [NOTIFICATION_EMAIL]},
            Message={
                'Subject': {'Data': email_subject},
                'Body': {'Text': {'Data': email_body}}
            }
        )
        
        # Send confirmation email to user
        user_email_body = f"""
Hi {contact_name},

Thank you for your interest in TradeRamp! We've received your request to schedule a 25-minute strategy call.

We'll contact you within 24 hours at {phone} to schedule a time that works for you.

In the meantime, here's what you can expect from our call:
- Review of your current marketing efforts
- Analysis of your local market opportunity  
- Custom growth strategy for your {trade_type} business
- Clear next steps with no pressure

Looking forward to speaking with you!

Best regards,
The TradeRamp Team
"""
        
        ses.send_email(
            Source=FROM_EMAIL,
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': 'TradeRamp - Call Scheduling Confirmation'},
                'Body': {'Text': {'Data': user_email_body}}
            }
        )
        
        # Success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Success! We\'ll contact you within 24 hours.',
                'status': 'success'
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Sorry, there was an error processing your request. Please try again or call us directly.',
                'status': 'error'
            })
        }

def lambda_handler_options(event, context):
    """Handle CORS preflight requests"""
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': ''
    }