# test_emergency_detection.py
# Run this to test your fixed emergency detection

from app.services.rag_service import RAGService

def test_emergency_detection():
    """Test the fixed emergency detection logic"""
    
    rag = RAGService()
    
    # Test cases that should NOT be emergencies
    non_emergency_tests = [
        "What items should be in an emergency kit?",
        "What's the current fire danger level?",
        "How can I prepare for winter storms?",
        "Tips for staying safe during festivals?",
        "What kind of emergencies can you help with?",
        "Are you connected to 911?",
        "Can you track crime trends?",
        "What kind of emergencies can you help with? Are you connected to 911? Can you track crime trends?",
        "Tell me about fire safety",
        "How to prepare for emergencies",
        "What should I do in case of emergency?",
        "Safety tips for downtown Indianapolis"
    ]
    
    # Test cases that SHOULD be emergencies
    emergency_tests = [
        "There's a fire in my house right now",
        "Car accident just happened on I-65",
        "Someone is breaking in help me",
        "Gas leak emergency call 911",
        "Help me someone is attacking me",
        "Medical emergency happening now",
        "I need help urgent emergency",
        "Call 911 now please"
    ]
    
    print("🧪 Testing NON-emergency detection (should NOT trigger emergency):")
    print("=" * 70)
    
    for test_message in non_emergency_tests:
        result = rag._classify_user_intent(test_message)
        intent = result['intent']
        emergency = result.get('emergency', False)
        
        status = "✅ PASS" if not emergency else "❌ FAIL"
        print(f"{status} | '{test_message[:50]}...' → {intent} (emergency: {emergency})")
    
    print("\n" + "=" * 70)
    print("🚨 Testing EMERGENCY detection (SHOULD trigger emergency):")
    print("=" * 70)
    
    for test_message in emergency_tests:
        result = rag._classify_user_intent(test_message)
        intent = result['intent']
        emergency = result.get('emergency', False)
        
        status = "✅ PASS" if emergency else "❌ FAIL"
        print(f"{status} | '{test_message[:50]}...' → {intent} (emergency: {emergency})")
    
    print("\n" + "=" * 70)
    print("🤖 Testing CAPABILITY questions:")
    print("=" * 70)
    
    capability_tests = [
        "What do you do?",
        "How can you help me?",
        "Are you connected to 911?",
        "What kind of emergencies can you help with?"
    ]
    
    for test_message in capability_tests:
        result = rag._classify_user_intent(test_message)
        intent = result['intent']
        
        status = "✅ PASS" if intent == 'bot_capabilities' else "❌ FAIL"
        print(f"{status} | '{test_message}' → {intent}")
    
    print("\n" + "=" * 70)
    print("❓ Testing MULTIPLE questions:")
    print("=" * 70)
    
    multi_tests = [
        "What can you do? Are you connected to 911? Can you track crime?",
        "How do I report potholes? What about street lights? Who do I call?"
    ]
    
    for test_message in multi_tests:
        result = rag._classify_user_intent(test_message)
        intent = result['intent']
        
        status = "✅ PASS" if intent == 'multiple_questions' else "❌ FAIL"
        print(f"{status} | '{test_message[:50]}...' → {intent}")

if __name__ == "__main__":
    print("🔧 SafeIndy Assistant - Emergency Detection Test")
    print("Testing the fixed emergency classification logic...\n")
    
    try:
        test_emergency_detection()
        print("\n✅ Test completed! Review the results above.")
        print("❌ FAIL items need attention - ✅ PASS items are working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print("Make sure your RAG service is properly configured.")

# Additional manual test function
def quick_test(message):
    """Quick test a single message"""
    rag = RAGService()
    result = rag._classify_user_intent(message)
    
    print(f"Message: '{message}'")
    print(f"Intent: {result['intent']}")
    print(f"Emergency: {result.get('emergency', False)}")
    print(f"Confidence: {result['confidence']}")
    print(f"Reasoning: {result.get('reasoning', 'N/A')}")
    print("-" * 50)