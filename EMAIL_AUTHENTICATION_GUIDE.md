# Email Authentication Setup Guide

## 🚨 CRITICAL: Why Your Email is Being Rejected

Gmail and other major email providers **require proper email authentication** to prevent spam. The error you received indicates:

1. **DKIM authentication failed** - Your DKIM signature is not valid
2. **SPF authentication failed** - Your sending IP is not authorized  
3. **Domain not properly configured** - Authentication records are missing

## 🔧 How to Fix Email Authentication Issues

### Option 1: Use Your Own Domain (Recommended)

If you own a domain (e.g., `yourdomain.com`), follow these steps:

#### Step 1: Set Up DNS Records
1. Go to the **"DNS Setup"** tab in the application
2. Enter your domain name (e.g., `yourdomain.com`)
3. Click **"Generate DNS Records"**
4. Add the generated SPF, DKIM, and DMARC records to your domain's DNS settings

#### Step 2: DNS Record Examples
```
# SPF Record (TXT)
Name: yourdomain.com
Type: TXT
Value: v=spf1 ip4:YOUR_SERVER_IP include:_spf.google.com -all

# DKIM Record (TXT)  
Name: default._domainkey.yourdomain.com
Type: TXT
Value: v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...

# DMARC Record (TXT)
Name: _dmarc.yourdomain.com  
Type: TXT
Value: v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com
```

#### Step 3: Wait for DNS Propagation
- DNS changes can take 24-48 hours to propagate globally
- Use the **"Auth Check"** tab to verify your domain's authentication status

#### Step 4: Send Test Email
- Use `your-name@yourdomain.com` as the **FROM** address
- Never use Gmail/Yahoo/Outlook addresses as the FROM address

### Option 2: Testing with Safe Domains

For testing purposes, you can try sending:

1. **To test email servers** (these might accept emails):
   - `test@example.com` 
   - Internal email addresses within your organization

2. **From safe domains**:
   - Use subdomains like `test.yourdomain.com`
   - Use domains you control

### Option 3: Email Testing Services

For development/testing, consider using:
- **Mailtrap.io** - Email testing service
- **MailHog** - Local email testing server
- **Gmail SMTP** - Use Gmail's SMTP server (requires app password)

## 🔍 Understanding Email Authentication

### SPF (Sender Policy Framework)
- **Purpose**: Authorizes which IP addresses can send emails for your domain
- **Status**: Your server IP must be included in the SPF record

### DKIM (DomainKeys Identified Mail)
- **Purpose**: Cryptographically signs emails to verify authenticity
- **Status**: Requires matching public/private key pairs

### DMARC (Domain-based Message Authentication)
- **Purpose**: Policy for handling emails that fail SPF/DKIM checks
- **Status**: Tells receiving servers what to do with unauthenticated emails

## 🚫 Common Mistakes to Avoid

1. **Using Gmail/Yahoo as FROM address**
   - ❌ `from_email: "you@gmail.com"`  
   - ✅ `from_email: "you@yourdomain.com"`

2. **Missing DNS records**
   - All three records (SPF, DKIM, DMARC) are required

3. **Incorrect IP address in SPF**
   - Must include your actual server IP

4. **Testing immediately after DNS changes**
   - Wait 24-48 hours for propagation

## 🧪 Testing Your Setup

1. **Use the Auth Check tab** to verify your domain
2. **Send test emails** to your own addresses first
3. **Check email headers** in received emails to verify DKIM signatures
4. **Use online tools** like MXToolbox to verify DNS records

## 📧 Alternative: Use Established Email Services

For production use, consider:
- **SendGrid** - Email delivery service
- **Mailgun** - Email API service  
- **Amazon SES** - AWS email service
- **Postmark** - Transactional email service

These services handle authentication automatically and have better deliverability rates.

## 🔧 Current System Capabilities

Your email service system has:
- ✅ Raw socket SMTP implementation
- ✅ DKIM signing capability
- ✅ DNS MX record resolution
- ✅ SPF record generation
- ✅ DMARC policy generation
- ✅ Multi-user mailbox system

The system works correctly - the issue is with **authentication setup**, not the code!