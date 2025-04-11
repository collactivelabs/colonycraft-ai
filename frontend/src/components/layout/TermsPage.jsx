import React from 'react';
import Header from './Header';
import Footer from './Footer';
import '../../styles/LegalPages.css';

const TermsPage = () => {
  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <div className="legal-container">
          <h1>Terms of Service</h1>
          <p className="last-updated">Last Updated: April 11, 2025</p>

          <section className="legal-section">
            <h2>1. Introduction</h2>
            <p>
              Welcome to ColonyCraft AI ("we," "our," or "us"). These Terms of Service ("Terms") govern your access to and use of our website, applications, API, and services (collectively, the "Services").
            </p>
            <p>
              By accessing or using our Services, you agree to be bound by these Terms. If you do not agree to these Terms, you may not access or use the Services.
            </p>
          </section>

          <section className="legal-section">
            <h2>2. Definitions</h2>
            <p>
              <strong>"Account"</strong> means a unique account created for you to access our Services.
            </p>
            <p>
              <strong>"API"</strong> means our application programming interface that allows you to programmatically access our Services.
            </p>
            <p>
              <strong>"Content"</strong> means any text, images, or other material that you upload, generate, or otherwise provide through our Services.
            </p>
            <p>
              <strong>"LLM Providers"</strong> means third-party providers of large language models and AI services that are accessible through our Services.
            </p>
          </section>

          <section className="legal-section">
            <h2>3. Account Registration and Security</h2>
            <p>
              To use certain features of the Services, you may need to register for an Account. You agree to provide accurate, current, and complete information during the registration process and to update such information to keep it accurate, current, and complete.
            </p>
            <p>
              You are responsible for safeguarding your Account credentials and for any activities or actions under your Account. You agree to notify us immediately of any unauthorized access to or use of your Account.
            </p>
            <p>
              We reserve the right to disable any user account, at any time, if in our opinion you have failed to comply with these Terms.
            </p>
          </section>

          <section className="legal-section">
            <h2>4. API Keys and Usage</h2>
            <p>
              Our Services may allow you to generate and manage API keys for accessing various LLM Providers. You are responsible for keeping your API keys secure and not sharing them with unauthorized parties.
            </p>
            <p>
              Each API key may have certain rate limits, quotas, and other restrictions. You agree not to attempt to circumvent these limitations.
            </p>
            <p>
              We reserve the right to revoke or disable any API key at any time for any reason, including but not limited to, violation of these Terms or suspected fraudulent, abusive, or harmful activity.
            </p>
          </section>

          <section className="legal-section">
            <h2>5. Acceptable Use Policy</h2>
            <p>
              You agree not to use the Services to:
            </p>
            <ul>
              <li>Violate any applicable law or regulation</li>
              <li>Infringe the intellectual property rights of others</li>
              <li>Send spam or other unsolicited messages</li>
              <li>Upload or distribute malware or other harmful code</li>
              <li>Interfere with or disrupt the integrity or performance of the Services</li>
              <li>Attempt to gain unauthorized access to the Services or related systems</li>
              <li>Generate or distribute content that is illegal, harmful, threatening, abusive, harassing, defamatory, vulgar, obscene, invasive of privacy, or otherwise objectionable</li>
              <li>Use the Services to develop models or technologies that compete with ColonyCraft AI</li>
              <li>Use the Services to harm, threaten, or harass any person or group</li>
            </ul>
          </section>

          <section className="legal-section">
            <h2>6. Content and Intellectual Property</h2>
            <p>
              You retain all rights to your Content. By providing Content to the Services, you grant us a worldwide, non-exclusive, royalty-free license to use, reproduce, modify, adapt, publish, translate, and distribute your Content solely for the purpose of providing the Services to you.
            </p>
            <p>
              You represent and warrant that:
            </p>
            <ul>
              <li>You own or have the necessary rights to your Content</li>
              <li>Your Content does not violate the privacy rights, publicity rights, intellectual property rights, or other rights of any person</li>
              <li>Your Content does not contain material that is false, defamatory, or misleading</li>
            </ul>
            <p>
              We respect intellectual property rights and expect our users to do the same. If you believe that your copyrighted work has been copied in a way that constitutes copyright infringement, please contact us at legal@colonycraft.ai.
            </p>
          </section>

          <section className="legal-section">
            <h2>7. Third-Party LLM Providers</h2>
            <p>
              Our Services provide access to various third-party LLM Providers. The use of these LLM Providers is subject to their own terms and conditions, which you may be required to accept.
            </p>
            <p>
              We are not responsible for the content, accuracy, quality, legality, availability, or reliability of any LLM Provider or the content they generate.
            </p>
            <p>
              We reserve the right to add, remove, or modify the available LLM Providers at any time.
            </p>
          </section>

          <section className="legal-section">
            <h2>8. Billing and Payment</h2>
            <p>
              You agree to pay all fees associated with your use of the Services. We may change our fees at any time by posting the changes on our website or by notifying you directly.
            </p>
            <p>
              For subscription-based Services, you authorize us to charge your payment method on a recurring basis until your subscription is terminated.
            </p>
            <p>
              If we cannot charge your payment method for any reason, we reserve the right to suspend or terminate your access to the Services.
            </p>
            <p>
              All fees are exclusive of taxes, which you are responsible for paying.
            </p>
          </section>

          <section className="legal-section">
            <h2>9. Limitation of Liability</h2>
            <p>
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, IN NO EVENT SHALL COLONYCRAFT AI, ITS DIRECTORS, EMPLOYEES, PARTNERS, AGENTS, SUPPLIERS, OR AFFILIATES BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING WITHOUT LIMITATION, LOSS OF PROFITS, DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES, RESULTING FROM (I) YOUR ACCESS TO OR USE OF OR INABILITY TO ACCESS OR USE THE SERVICES; (II) ANY CONDUCT OR CONTENT OF ANY THIRD PARTY ON THE SERVICES; (III) ANY CONTENT OBTAINED FROM THE SERVICES; AND (IV) UNAUTHORIZED ACCESS, USE, OR ALTERATION OF YOUR TRANSMISSIONS OR CONTENT, WHETHER BASED ON WARRANTY, CONTRACT, TORT (INCLUDING NEGLIGENCE), OR ANY OTHER LEGAL THEORY, WHETHER OR NOT WE HAVE BEEN INFORMED OF THE POSSIBILITY OF SUCH DAMAGE.
            </p>
          </section>

          <section className="legal-section">
            <h2>10. Disclaimer of Warranties</h2>
            <p>
              THE SERVICES ARE PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, OR COURSE OF PERFORMANCE.
            </p>
            <p>
              COLONYCRAFT AI DOES NOT WARRANT THAT THE SERVICES WILL BE UNINTERRUPTED, SECURE, OR ERROR-FREE, THAT DEFECTS WILL BE CORRECTED, OR THAT THE SERVICES OR THE SERVERS THAT MAKE THE SERVICES AVAILABLE ARE FREE OF VIRUSES OR OTHER HARMFUL COMPONENTS.
            </p>
          </section>

          <section className="legal-section">
            <h2>11. Termination</h2>
            <p>
              We may terminate or suspend your account and access to the Services immediately, without prior notice or liability, for any reason, including without limitation if you breach the Terms.
            </p>
            <p>
              Upon termination, your right to use the Services will immediately cease. If you wish to terminate your account, you may simply discontinue using the Services or contact us at support@colonycraft.ai.
            </p>
          </section>

          <section className="legal-section">
            <h2>12. Changes to Terms</h2>
            <p>
              We reserve the right to modify or replace these Terms at any time. The most current version will be posted on our website. If a revision is material, we will try to provide at least 30 days' notice prior to any new terms taking effect.
            </p>
            <p>
              Your continued use of the Services after any changes to the Terms constitutes your acceptance of such changes.
            </p>
          </section>

          <section className="legal-section">
            <h2>13. Contact Information</h2>
            <p>
              If you have any questions about these Terms, please contact us at legal@colonycraft.ai.
            </p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default TermsPage;