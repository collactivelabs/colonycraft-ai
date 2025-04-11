import React from 'react';
import Header from './Header';
import Footer from './Footer';
import '../../styles/LegalPages.css';

const PrivacyPage = () => {
  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <div className="legal-container">
          <h1>Privacy Policy</h1>
          <p className="last-updated">Last Updated: April 11, 2025</p>

          <section className="legal-section">
            <h2>1. Introduction</h2>
            <p>
              At ColonyCraft AI ("we," "our," or "us"), we respect your privacy and are committed to protecting it through our compliance with this Privacy Policy.
            </p>
            <p>
              This Privacy Policy describes the types of information we may collect from you or that you may provide when you use our website, applications, API, and services (collectively, the "Services") and our practices for collecting, using, maintaining, protecting, and disclosing that information.
            </p>
            <p>
              Please read this Privacy Policy carefully to understand our policies and practices regarding your information. By accessing or using our Services, you agree to this Privacy Policy.
            </p>
          </section>

          <section className="legal-section">
            <h2>2. Information We Collect</h2>
            
            <h3>2.1 Information You Provide to Us</h3>
            <p>We may collect several types of information from and about users of our Services, including:</p>
            <ul>
              <li>Account information: When you register for an account, we collect your name, email address, and password.</li>
              <li>Profile information: Information you provide in your user profile, such as job title, company, or profile picture.</li>
              <li>Payment information: When you subscribe to our paid services, we collect payment details through our payment processors. We do not store full credit card information on our servers.</li>
              <li>Communications: If you contact us directly, we may collect information about your communication and any information you provide.</li>
              <li>API keys: We collect API keys that you provide for third-party LLM providers.</li>
              <li>User Content: The prompts, queries, and other information you submit to generate content through our Services.</li>
            </ul>
            
            <h3>2.2 Information We Collect Automatically</h3>
            <p>As you interact with our Services, we may automatically collect certain information about your equipment, browsing actions, and patterns, including:</p>
            <ul>
              <li>Usage details: We collect details of your visits to our Services, including traffic data, location data, logs, and other communication data and the resources that you access and use on the Services.</li>
              <li>Device information: We collect information about your device and internet connection, including your IP address, operating system, and browser type.</li>
              <li>Cookies and similar technologies: We use cookies and similar tracking technologies to collect information about your browsing activities over time.</li>
            </ul>
          </section>

          <section className="legal-section">
            <h2>3. How We Use Your Information</h2>
            <p>We use the information that we collect about you or that you provide to us, including any personal information:</p>
            <ul>
              <li>To provide, maintain, and improve our Services.</li>
              <li>To process your account creation and authenticate you when you log in.</li>
              <li>To route your requests to the appropriate LLM providers.</li>
              <li>To process your payments and prevent fraud.</li>
              <li>To provide you with support and respond to your inquiries.</li>
              <li>To personalize your experience with our Services.</li>
              <li>To send you technical notices, updates, security alerts, and administrative messages.</li>
              <li>To monitor and analyze usage patterns and trends.</li>
              <li>To enforce our Terms of Service and protect the rights, property, or safety of ColonyCraft AI, our users, or others.</li>
            </ul>
          </section>

          <section className="legal-section">
            <h2>4. Disclosure of Your Information</h2>
            <p>We may disclose personal information that we collect or you provide as described in this Privacy Policy:</p>
            <ul>
              <li>To third-party LLM providers to process your requests.</li>
              <li>To our subsidiaries and affiliates.</li>
              <li>To contractors, service providers, and other third parties we use to support our business.</li>
              <li>To a buyer or other successor in the event of a merger, divestiture, restructuring, reorganization, dissolution, or other sale or transfer of some or all of ColonyCraft AI's assets.</li>
              <li>To comply with any court order, law, or legal process, including to respond to any government or regulatory request.</li>
              <li>To enforce or apply our Terms of Service and other agreements.</li>
              <li>If we believe disclosure is necessary or appropriate to protect the rights, property, or safety of ColonyCraft AI, our users, or others.</li>
            </ul>
            
            <h3>4.1 User Content and LLM Providers</h3>
            <p>
              When you submit prompts or queries through our Services, this information is shared with the LLM provider you select. Each LLM provider has its own privacy policy governing how they handle your information. We encourage you to review the privacy policies of these providers.
            </p>
            <p>
              We do not use your prompts or the generated content to train our own models. However, depending on the LLM provider you select, your data may be subject to their data handling practices, which may include using your data for model training or improvement.
            </p>
          </section>

          <section className="legal-section">
            <h2>5. Data Security</h2>
            <p>
              We have implemented measures designed to secure your personal information from accidental loss and from unauthorized access, use, alteration, and disclosure. All information you provide to us is stored on secure servers behind firewalls.
            </p>
            <p>
              The safety and security of your information also depends on you. You are responsible for keeping your account password confidential. We ask you not to share your password with anyone.
            </p>
            <p>
              Unfortunately, the transmission of information via the internet is not completely secure. Although we do our best to protect your personal information, we cannot guarantee the security of your personal information transmitted to our Services. Any transmission of personal information is at your own risk.
            </p>
          </section>

          <section className="legal-section">
            <h2>6. Data Retention</h2>
            <p>
              We will retain your personal information for as long as necessary to fulfill the purposes for which we collected it, including for the purposes of satisfying any legal, accounting, or reporting requirements.
            </p>
            <p>
              To determine the appropriate retention period for personal information, we consider the amount, nature, and sensitivity of the personal information, the potential risk of harm from unauthorized use or disclosure of your personal information, the purposes for which we process your personal information and whether we can achieve those purposes through other means, and the applicable legal requirements.
            </p>
            <p>
              In some circumstances, we may anonymize your personal information so that it can no longer be associated with you, in which case we may use such information without further notice to you.
            </p>
          </section>

          <section className="legal-section">
            <h2>7. Your Rights and Choices</h2>
            <p>
              You have several rights and choices regarding your personal information:
            </p>
            <ul>
              <li>Account Information: You can review and change your personal information by logging into your account and visiting your account profile page.</li>
              <li>Cookies: Most web browsers are set to accept cookies by default. You can usually choose to set your browser to remove or reject browser cookies.</li>
              <li>Promotional Communications: You can opt out of receiving promotional communications from us by following the instructions in those communications.</li>
              <li>Data Access and Portability: You can request a copy of your personal information that we hold.</li>
              <li>Data Correction: You can request correction of your personal information if it is inaccurate or incomplete.</li>
              <li>Data Deletion: You can request deletion of your personal information, subject to certain exceptions.</li>
              <li>Objection: You can object to our processing of your personal information in certain circumstances.</li>
              <li>Withdrawal of Consent: Where we rely on your consent to process your personal information, you can withdraw your consent at any time.</li>
            </ul>
            <p>
              To exercise these rights, please contact us at privacy@colonycraft.ai.
            </p>
          </section>

          <section className="legal-section">
            <h2>8. Children's Privacy</h2>
            <p>
              Our Services are not intended for children under 16 years of age. We do not knowingly collect personal information from children under 16. If you are under 16, do not use or provide any information on our Services. If we learn we have collected or received personal information from a child under 16 without verification of parental consent, we will delete that information.
            </p>
          </section>

          <section className="legal-section">
            <h2>9. International Data Transfers</h2>
            <p>
              Your personal information may be transferred to, and processed in, countries other than the country in which you are resident. These countries may have data protection laws that are different from the laws of your country.
            </p>
            <p>
              Specifically, our servers are located in the United States, and our third-party LLM providers and service providers operate around the world. This means that when we collect your personal information, we may process it in any of these countries.
            </p>
            <p>
              However, we have taken appropriate safeguards to require that your personal information will remain protected in accordance with this Privacy Policy. These safeguards include implementing the European Commission's Standard Contractual Clauses for transfers of personal information between our group companies and third-party providers, which require them to protect personal information in accordance with European data protection law.
            </p>
          </section>

          <section className="legal-section">
            <h2>10. Changes to Our Privacy Policy</h2>
            <p>
              We may update our Privacy Policy from time to time. If we make material changes to how we treat our users' personal information, we will notify you through a notice on our website or by email.
            </p>
            <p>
              The date the Privacy Policy was last revised is identified at the top of the page. You are responsible for ensuring we have an up-to-date active and deliverable email address for you, and for periodically visiting our Services and this Privacy Policy to check for any changes.
            </p>
          </section>

          <section className="legal-section">
            <h2>11. Contact Information</h2>
            <p>
              To ask questions or comment about this Privacy Policy and our privacy practices, contact us at:
            </p>
            <p>
              privacy@colonycraft.ai
            </p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default PrivacyPage;