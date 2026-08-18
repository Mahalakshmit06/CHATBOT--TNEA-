# Campus AI 6.3 Chatbot Updates

- Added persistent **College type** to the counselling profile (Government, Private, Autonomous, University, and combined filters where supported).
- College-type preference now persists across follow-up questions and is applied to eligible-college recommendations.
- Chat recommendations now return **only records that are actually eligible** for the supplied cutoff/community/filter combination. Records without a published community cutoff are not presented as eligible recommendations.
- Removed automatic smooth scrolling after every message/typing-state change. The chat viewport stays where the user left it; the user controls scrolling inside the chat box.
- Increased the AI Counsellor panel width from 900px to 1080px while keeping the existing chat panel height/length behavior unchanged.
- Existing Home, AI Counsellor, College Finder and Cutoff Calculator UI structure is preserved.
- TNEA official counselling information remains grounded in official TNEA material; college-specific recommendations remain grounded in the project dataset.
