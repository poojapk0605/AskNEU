import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import './App.css';
import { marked } from 'marked';
import IntroModal from './IntroModal';
import HelpModal from './HelpModal';
import FeedbackModal from './FeedbackModal';
import { 
  MessageSquare, ChevronRight, X, Moon, Sun, Eye, EyeOff, 
  ThumbsUp, ThumbsDown, Copy, Radar, Send, BookOpen, School,
  HelpCircle
} from 'lucide-react';

// Memoized Message Component
const MessageComponent = memo(({
  message, 
  index, 
  setConversations,
  conversations,
  activeConversationId,
  submitFeedback, 
  copyToClipboard, 
  getFeedbackForMessage,
  activeFeedback,
  activeConversation,
  setActiveFeedback
}) => {
  const [activeTab, setActiveTab] = useState(message.activeTab || 'answer');
  const [feedbackAcknowledged, setFeedbackAcknowledged] = useState(false);

  // Get query_id directly from the message
  let query_id = message.query_id;
  if (!query_id && message.sender === 'bot') {
    console.warn(`Bot message at index ${index} has no query_id`);
    
    // For welcome message, use a fixed ID
    if (message.text && message.text.includes("Hi! I am Northeastern University Assistant")) {
      query_id = 'welcome_message';
      
      // Update the message with this query_id
      const updatedConversations = {...conversations};
      const currentConv = {...updatedConversations[activeConversationId]};
      currentConv.messages = Array.isArray(currentConv.messages) ? [...currentConv.messages] : [];
      
      if (index >= 0 && index < currentConv.messages.length) {
        currentConv.messages[index] = {
          ...currentConv.messages[index],
          query_id: query_id
        };
        updatedConversations[activeConversationId] = currentConv;
        setConversations(updatedConversations);
      }
    }
  }


  // Get current feedback state for this message
  const currentFeedback = query_id ? (
    activeFeedback[query_id] || 
    (activeConversation?.feedback && activeConversation.feedback[query_id])
  ) : null;

  // Set CSS classes for feedback buttons
  const thumbsUpClass = `action-btn thumbs-up ${currentFeedback === 'positive' ? 'active clicked' : ''}`;
  const thumbsDownClass = `action-btn thumbs-down ${currentFeedback === 'negative' ? 'active clicked' : ''}`;

  // Handle tab changes between answer and sources
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    const updatedConversations = {...conversations};
    const currentConv = {...updatedConversations[activeConversationId]};
    currentConv.messages = [...currentConv.messages];

    if (index >= 0 && index < currentConv.messages.length) {
      currentConv.messages[index] = {
        ...currentConv.messages[index],
        activeTab: tab
      };
      updatedConversations[activeConversationId] = currentConv;
      setConversations(updatedConversations);
    }
  };
  const makeLinksOpenInNewTab = (html) => {
	  // Create a temporary div
	  const temp = document.createElement('div');
	  temp.innerHTML = html;
	  
	  // Find all links and add target="_blank"
	  const links = temp.getElementsByTagName('a');
	  for (let i = 0; i < links.length; i++) {
		links[i].setAttribute('target', '_blank');
		links[i].setAttribute('rel', 'noopener noreferrer');
	  }
	  
	  return temp.innerHTML;
	};
  // Check if this response was from a namespace search
  // Only hide sources if the message has a responseNamespace that isn't 'default'
  const hideSourcesTab = message.responseNamespace && message.responseNamespace !== 'default';

  return (
    <div className={`message ${message.sender}`}>
      <div className="message-container">
        <div className="message-content">
          {message.sender === 'user' && (
            <div className="message-sender">You</div>
          )}

          {message.sender === 'bot' && (
            <>
              <div className="message-header">
                <div className="message-sender">
                  NEU Assistant
                  {message.searchMode === 'deepsearch' && (
                    <span className="processing-time">Deep Research</span>
                  )}
                </div>
                <div className="message-actions">
                  <button 
                    className="action-btn"
                    onClick={() => copyToClipboard(message.text)}
                    title="Copy to clipboard"
                    aria-label="Copy to clipboard"
                  >
                    <Copy size={16} />
                  </button>

                  {query_id && !query_id.startsWith('temp_msg_') && !query_id.startsWith('error_') && (
                    <>
                      {(!currentFeedback && !feedbackAcknowledged) && (
                        <>
                          <button 
                            className={thumbsUpClass}
                            onClick={() => {
                              setActiveFeedback(prev => ({ ...prev, [query_id]: 'positive' }));
                              submitFeedback(query_id, 'positive');
                              setFeedbackAcknowledged(true);
                              setTimeout(() => setFeedbackAcknowledged(false), 2000);
                            }}
                            title="This was helpful"
                          >
                            <ThumbsUp size={16} />
                          </button>
                          <button 
                            className={thumbsDownClass}
                            onClick={() => {
                              setActiveFeedback(prev => ({ ...prev, [query_id]: 'negative' }));
                              submitFeedback(query_id, 'negative');
                              setFeedbackAcknowledged(true);
                              setTimeout(() => setFeedbackAcknowledged(false), 2000);
                            }}
                            title="This was not helpful"
                          >
                            <ThumbsDown size={16} />
                          </button>
                        </>
                      )}

                      {/* Already submitted feedback view */}
                      {currentFeedback === 'positive' && (
                        <ThumbsUp 
                          className="action-btn thumbs-up active clicked" 
                          size={16} 
                          stroke="#cc0000" 
                          title="You marked this helpful" 
                        />
                      )}
                      {currentFeedback === 'negative' && (
                        <ThumbsDown 
                          className="action-btn thumbs-down active clicked" 
                          size={16} 
                          stroke="#cc0000" 
                          title="You marked this not helpful" 
                        />
                      )}
                    </>
                  )}

                  {feedbackAcknowledged && (
                    <div className="feedback-thanks">Thank you for your feedback!</div>
                  )}
                </div>
              </div>

              {/* Only show tabs if this response wasn't from a namespace search */}
              {!hideSourcesTab && (
                <div className="message-tabs">
                  <button 
                    className={`tab ${activeTab === 'answer' ? 'active' : ''}`}
                    onClick={() => handleTabChange('answer')}
                  >
                    Answer
                  </button>
                  <button 
                    className={`tab ${activeTab === 'sources' ? 'active' : ''}`}
                    onClick={() => handleTabChange('sources')}
                  >
                    Sources
                  </button>
                </div>
              )}
            </>
          )}

          <div className="message-text">
            {message.sender === 'bot' ? (
              (activeTab === 'sources' && !hideSourcesTab) ? (
                message.sources ? (
				  <div className="sources" dangerouslySetInnerHTML={{ __html: makeLinksOpenInNewTab(marked.parse(message.sources || '')) }} />
				) : (
				  <div className="no-sources">No sources available for this response.</div>
				  )
				) : (
				  <div dangerouslySetInnerHTML={{ __html: makeLinksOpenInNewTab(marked.parse(message.text || '')) }} />
              )
            ) : (
              message.text
            )}
          </div>
        </div>
      </div>
    </div>
  );
});
// Default conversation template
const DEFAULT_CONVERSATION = {
  id: 'new',
  title: 'New Chat',
  messages: [{
    sender: 'bot',
    text: "Hi! I am Northeastern University Assistant. What can I help with?",
    activeTab: 'answer',
    query_id: 'welcome_message',
    showInitialMessage: true
  }],
  date: new Date().toISOString(),
  feedback: {}
};

// Cloud storage service - simplified
const cloudStorage = {
  async saveConversations(userId, conversations) {
    try {
      const response = await fetch('/api/conversations/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, conversations }),
      });
      return response.ok;
    } catch (error) {
      console.warn('Error saving conversations:', error);
      return false;
    }
  },
  
  async loadConversations(userId) {
    try {
      const response = await fetch(`/api/conversations/load?userId=${userId}`);
      if (!response.ok) return null;
      const data = await response.json();
      return data.conversations;
    } catch (error) {
      console.warn('Error loading conversations:', error);
      return null;
    }
  },
  
  async saveActiveConversation(userId, conversationId) {
    try {
      const response = await fetch('/api/conversations/active', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, activeConversationId: conversationId }),
      });
      return response.ok;
    } catch (error) {
      console.warn('Error saving active conversation:', error);
      return false;
    }
  },
  
  async loadActiveConversation(userId) {
    try {
      const response = await fetch(`/api/conversations/active?userId=${userId}`);
      if (!response.ok) return null;
      const data = await response.json();
      return data.activeConversationId;
    } catch (error) {
      console.warn('Error loading active conversation:', error);
      return null;
    }
  }
};

// Main App component
function App({ user, onLogout }) {
  // State for modals
  const [showIntroModal, setShowIntroModal] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  
  // User ID for storage
  const [userId, setUserId] = useState(() => {
    if (user?.userId) return user.userId;
    const existing = sessionStorage.getItem('userId');
    if (existing) return existing;
    const newId = `user_${Date.now()}`;
    sessionStorage.setItem('userId', newId);
    return newId;
  });

  // Theme and chat settings
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('darkMode') === 'true');
  const [incognitoMode, setIncognitoMode] = useState(false);
  const [deepSearchMode, setDeepSearchMode] = useState(false);
  const [namespace, setNamespace] = useState("default");
  const [searchMode, setSearchMode] = useState("direct");

  // Namespace labels and info
  const namespaceLabels = {
    default: "Default",
    course: "Course Offerings",
    classroom: "Study Spot Finder"
  };
  
  const namespaceUpdateInfo = {
	  course: {
		desktop: "Last updated: Fall 2025 offerings",
		mobile: "Fall 2025 offerings"
	  },
	  classroom: {
		desktop: "Last updated: Spring 2025 schedule",
		mobile: "Spring 2025 schedule"
	  }
  };

  // Conversation states
  const [activeFeedback, setActiveFeedback] = useState({});
  const [activeConversationId, setActiveConversationId] = useState('new');
  const [conversations, setConversations] = useState({ new: {...DEFAULT_CONVERSATION} });

  // UI states
  const [isInitializing, setIsInitializing] = useState(true);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false); // Start collapsed

  // References for DOM elements
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Logout handler
  const handleLogout = () => {
    sessionStorage.clear();
    localStorage.removeItem('activeConversationId');
    setConversations({ new: {...DEFAULT_CONVERSATION} });
    setActiveConversationId('new');
    setActiveFeedback({});
    setUserId(`user_${Date.now()}`);
    if (onLogout) onLogout();
    window.location.href = '/';
  };
  const getPlaceholderText = () => {
	  switch(namespace) {
		case 'course':
		  return "Find any course offering";
		case 'classroom':
		  return "Specify day, time, and room if possible";
		default:
		  return "Ask anything about Northeastern University — we've got you covered!";
	  }
  };
  // Save conversations to server
  const saveConversationsToServer = async () => {
    if (isInitializing || incognitoMode) return;
    
    try {
      const nonIncognitoConversations = {};
      Object.entries(conversations).forEach(([id, conv]) => {
        if (!conv.isIncognito) {
          nonIncognitoConversations[id] = conv;
        }
      });
      
      await cloudStorage.saveConversations(userId, nonIncognitoConversations);
      
      if (!conversations[activeConversationId]?.isIncognito) {
        await cloudStorage.saveActiveConversation(userId, activeConversationId);
      }
    } catch (error) {
      console.error("Error saving conversations:", error);
    }
  };

  // Update user ID when the user changes
  useEffect(() => {
    if (user?.userId && user.userId !== userId) {
      setUserId(user.userId);
      sessionStorage.setItem('userId', user.userId);
    }
  }, [user?.userId, userId]);

  // Check for user changes on initial load
  useEffect(() => {
    const storedUser = sessionStorage.getItem('previousUser');
    const currentUser = user?.userId || 'guest';
    
    if (storedUser && storedUser !== currentUser) {
      console.log("User changed - resetting state");
      setConversations({ new: {...DEFAULT_CONVERSATION} });
      setActiveConversationId('new');
      setActiveFeedback({});
    }
    
    sessionStorage.setItem('previousUser', currentUser);
  }, [user?.userId]);
  
  // Show intro modal for new users
  useEffect(() => {
    if (userId) {
      const seen = localStorage.getItem(`seenIntro_${userId}`);
      if (!seen) {
        setShowIntroModal(true);
        localStorage.setItem(`seenIntro_${userId}`, 'true');
      }
      
      // For first time users, collapse sidebar by default
      const seenApp = localStorage.getItem(`seenApp_${userId}`);
      if (!seenApp) {
        setSidebarOpen(false);
        localStorage.setItem(`seenApp_${userId}`, 'true');
      }
    }
  }, [userId]);

  // Load conversations on initialization
  useEffect(() => {
    if (isInitializing && !incognitoMode) {
      const currentUserId = user?.userId || userId;
      
      Promise.all([
        cloudStorage.loadConversations(currentUserId),
        cloudStorage.loadActiveConversation(currentUserId)
      ]).then(([loadedConvs, activeId]) => {
        if (loadedConvs && Object.keys(loadedConvs).length > 0) {
          setConversations(loadedConvs);
          
          if (activeId && loadedConvs[activeId]) {
            setActiveConversationId(activeId);
          } else {
            const firstId = Object.keys(loadedConvs)[0];
            setActiveConversationId(firstId || 'new');
          }
        }
        
        setIsInitializing(false);
      }).catch(err => {
        console.error("Error initializing:", err);
        setIsInitializing(false);
      });
    }
  }, [isInitializing, incognitoMode, userId, user]);
 
  // Get current active conversation with fallback
  const activeConversation =
    conversations && conversations[activeConversationId] && Array.isArray(conversations[activeConversationId].messages)
      ? conversations[activeConversationId]
      : conversations && conversations.new && Array.isArray(conversations.new.messages)
        ? conversations.new
        : { ...DEFAULT_CONVERSATION };

  // Get suggested questions based on namespace
  const getSuggestedQuestions = () => {
    if (namespace === 'course') {
      return [
        "What are the class timings and classroom location for CHEM 1211: General Chemistry 1?",
        "Could you provide more details about LAW 6403: Constitutional Law?",
        "Which professor is teaching CS 5500: Data Science Capstone during the fall semester?",
        "What are the prerequisites for ESLG 0130: Community Learning 2?"
      ];
    } else if (namespace === 'classroom') {
      return [
        "Can you suggest a good study spot on campus for Monday at 2 PM where I can stay for a few hours?",
        "What are my options for finding a study spot in Churchill Hall on Monday afternoon?",
        "International Village 018 available for study for one hour on Monday ?",
        "Can you give me the class schedule for Room 229 in Richards Hall on Monday?"
      ];
    } else {
      return [
        "How can I request a new Northeastern ID card?",
        "How do I waive my Northeastern health insurance?",
        "As an international student, can I work as both a Teaching Assistant (TA) and a Research Assistant (RA) at the same time?",
        "What parking options are available on Boston campus?"
      ];
    }
  };

  // Save conversations with debouncing
  useEffect(() => {
    const saveTimer = setTimeout(saveConversationsToServer, 500);
    return () => clearTimeout(saveTimer);
  }, [conversations, activeConversationId, userId, incognitoMode, isInitializing]);

  // Auto scroll when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeConversation?.messages?.length]);

  // Auto resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  // Apply dark mode
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-theme');
    } else {
      document.body.classList.remove('dark-theme');
    }
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);

  // Set document title
  useEffect(() => {
    document.title = "askNEU";
  }, []);
  
  // Register guest users
  useEffect(() => {
    const registerGuestUser = async () => {
      if (userId && (userId.startsWith('user_') || userId.startsWith('guest_'))) {
        try {
          await fetch('/api/users/guest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              guestId: userId,
              timestamp: new Date().toISOString()
            })
          });
        } catch (err) {
          // Silent fail - conversation saving will still work
        }
      }
    };
    
    if (userId && !isInitializing) {
      registerGuestUser();
    }
  }, [userId, isInitializing]);
  
  // Hide greeting message after first user message
  useEffect(() => {
    if (activeConversation?.messages?.length > 1 && 
      activeConversation.messages[0].showInitialMessage) {
      const updatedConversations = { ...conversations };
      const currentConv = { ...updatedConversations[activeConversationId] };
      if (!Array.isArray(currentConv.messages)) currentConv.messages = [];
      
      if (currentConv?.messages?.length > 0) {
        currentConv.messages[0] = {
          ...currentConv.messages[0],
          showInitialMessage: false
        };
      }
      
      updatedConversations[activeConversationId] = currentConv;
      setConversations(updatedConversations);
    }
  }, [activeConversation?.messages?.length, activeConversationId, conversations]);

  // Send a message to the backend
  const sendMessage = async () => {
    if (!input.trim()) return;

    // Update conversations state
    const updatedConversations = { ...conversations };
    const currentConv = { ...updatedConversations[activeConversationId] };
    
    // Ensure messages array exists
    if (!Array.isArray(currentConv.messages)) {
      currentConv.messages = [];
    }
    
    // Update title if first user message
    if (!currentConv.title || currentConv.title === 'New Chat') {
      currentConv.title = input.length > 30 
        ? input.substring(0, 30) + '...' 
        : input;
    }
    
    // Add user message
    currentConv.messages.push({ 
      sender: 'user', 
      text: input, 
      timestamp: new Date().toISOString() 
    });
    
    updatedConversations[activeConversationId] = currentConv;
    setConversations(updatedConversations);
    
    // Clear input and set loading
    setInput('');
    setIsLoading(true);

    // Make API request
    try {
      const actualSearchMode = deepSearchMode ? "deepsearch" : searchMode;
      
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: input, 
          namespace: namespace, 
          search_mode: actualSearchMode,
          userId: userId
        })
      });
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data = await res.json();
      
      // Update with bot response
      const withResponseConversations = { ...updatedConversations };
      const withResponseConv = { ...withResponseConversations[activeConversationId] };
      
      // Create bot message
	  const responseMessage = { 
		  sender: 'bot', 
		  text: data.answer || "Sorry, I couldn't generate a response.",
		  timestamp: new Date().toISOString(),
		  sources: Array.isArray(data.sources) ? data.sources.join("\n") : (data.sources || ""),
		  query_id: data.query_id,
		  processingTime: data.processing_time || 0,
		  searchMode: data.search_mode || actualSearchMode,
		  responseNamespace: namespace, // Add this line
		  activeTab: 'answer'
	  };
      
      withResponseConv.messages.push(responseMessage);
      
      // Initialize feedback
      if (!withResponseConv.feedback) {
        withResponseConv.feedback = {};
      }
      
      withResponseConversations[activeConversationId] = withResponseConv;
      setConversations(withResponseConversations);

    } catch (err) {
      console.error("Error in API call:", err.message);
      
      // Add error message
      const withErrorConversations = { ...updatedConversations };
      const withErrorConv = { ...withErrorConversations[activeConversationId] };
      
      const errorResponseMessage = { 
        sender: 'bot', 
        text: 'Could not contact backend. Check connection or try again later.',
        timestamp: new Date().toISOString(),
        query_id: `error_${Date.now()}`,
        activeTab: 'answer'
      };
      
      withErrorConv.messages.push(errorResponseMessage);
      withErrorConversations[activeConversationId] = withErrorConv;
      setConversations(withErrorConversations);
      
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Enter key in textarea
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // UI toggle functions
  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
  const toggleDarkMode = () => setDarkMode(!darkMode);
  const toggleDeepSearch = () => setDeepSearchMode(!deepSearchMode);
  
  // Set namespace or perform action
  const handleSpecialAction = (action) => {
    if (action === "course" || action === "classroom") {
      setNamespace(prev => (prev === action ? "default" : action));
    } else if (action === "deepsearch") {
      setDeepSearchMode(true);
    }
  };
  
  // Toggle incognito mode
  const toggleIncognitoMode = () => {
    if (!incognitoMode) {
      // Entering incognito mode
      setIncognitoMode(true);
      startNewChat();
    } else {
      // Exiting incognito mode
      const updatedConversations = {};
      Object.entries(conversations).forEach(([id, conv]) => {
        if (!conv.isIncognito) {
          updatedConversations[id] = conv;
        }
      });
      
      setConversations(updatedConversations);
      
      if (conversations[activeConversationId]?.isIncognito) {
        const nonIncognitoIds = Object.keys(updatedConversations);
        if (nonIncognitoIds.length > 0) {
          setActiveConversationId(nonIncognitoIds[0]);
        } else {
          setIncognitoMode(false);
          startNewChat();
          return;
        }
      }
      
      // Load saved conversations
      cloudStorage.loadConversations(userId).then(storedConversations => {
        if (storedConversations) {
          setConversations(storedConversations);
          
          cloudStorage.loadActiveConversation(userId).then(storedActiveId => {
            if (storedActiveId && storedConversations[storedActiveId]) {
              setActiveConversationId(storedActiveId);
            }
          });
        }
      });
      
      setIncognitoMode(false);
    }
  };
	
  // Handle suggested question click
  const handleSuggestedQuestion = (question) => {
    // Add the user message
    const updatedConversations = { ...conversations };
    const currentConv = { ...updatedConversations[activeConversationId] };
    if (!Array.isArray(currentConv.messages)) currentConv.messages = [];
    
    // Update title if first message
    if (!currentConv.title || currentConv.title === 'New Chat') {
      currentConv.title = question.length > 30 
        ? question.substring(0, 30) + '...' 
        : question;
    }
    
    // Add message
    currentConv.messages.push({ 
      sender: 'user', 
      text: question, 
      timestamp: new Date().toISOString() 
    });
    
    updatedConversations[activeConversationId] = currentConv;
    setConversations(updatedConversations);
    
    // Clear input and set loading
    setInput('');
    setIsLoading(true);
    
    // Send message to API
    const actualSearchMode = deepSearchMode ? "deepsearch" : searchMode;
    
    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        query: question,
        namespace: namespace,
        search_mode: actualSearchMode,
        userId: userId
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      // Update with bot response
      const withResponseConversations = { ...updatedConversations };
      const withResponseConv = { ...withResponseConversations[activeConversationId] };
      
	  const responseMessage = { 
		  sender: 'bot', 
		  text: data.answer || "Sorry, I couldn't generate a response.",
		  timestamp: new Date().toISOString(),
		  sources: Array.isArray(data.sources) ? data.sources.join("\n") : (data.sources || ""),
		  query_id: data.query_id,
		  processingTime: data.processing_time || 0,
		  searchMode: data.search_mode || actualSearchMode,
		  responseNamespace: namespace, // Add the namespace that was used for this response
		  activeTab: 'answer'
	  };      
      withResponseConv.messages.push(responseMessage);
      
      // Initialize feedback
      if (!withResponseConv.feedback) {
        withResponseConv.feedback = {};
      }
      
      withResponseConversations[activeConversationId] = withResponseConv;
      setConversations(withResponseConversations);
      setIsLoading(false);
    })
    .catch(error => {
      console.error('Error in API call:', error);
      
      // Add error message
      const updatedWithError = { ...updatedConversations };
      const convWithError = { ...updatedWithError[activeConversationId] };
      
      convWithError.messages.push({ 
        sender: 'bot', 
        text: 'Sorry, I encountered an error connecting to the backend.',
        timestamp: new Date().toISOString(),
        query_id: `error_${Date.now()}`,
        activeTab: 'answer'
      });
      
      updatedWithError[activeConversationId] = convWithError;
      setConversations(updatedWithError);
      setIsLoading(false);
    });
  };
  
  // Start a new chat
  const startNewChat = () => {
    const newId = 'conv_' + Date.now();

    const newConversation = {
      id: newId,
      title: 'New Chat',
      messages: [{
        sender: 'bot',
        text: "Hi! I am Northeastern University Assistant. What can I help with?",
        activeTab: 'answer',
        query_id: 'welcome_message',
        showInitialMessage: true
      }],
      date: new Date().toISOString(),
      feedback: {},
      userId: userId,
      isIncognito: incognitoMode
    };

    setConversations(prev => ({
      ...prev,
      [newId]: newConversation
    }));

    setActiveConversationId(newId);
    setActiveFeedback({});
    setInput('');
  };

  const selectConversation = (id) => {
    setActiveConversationId(id);
  };
  
  // Delete a conversation
  const deleteConversation = async (id, e) => {
    e.stopPropagation();

    const isIncognitoChat = conversations[id]?.isIncognito;

    try {
      // Only delete from DB if not incognito
      if (!isIncognitoChat) {
        await fetch('/api/conversations/delete', {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ userId, conversationId: id })
        });
      }
    } catch (error) {
      console.error('Error deleting conversation from server:', error);
    }

    // Update state
    const updatedConversations = { ...conversations };
    delete updatedConversations[id];
    setConversations(updatedConversations);

    // Reset active chat if needed
    if (id === activeConversationId) {
      const remainingIds = Object.keys(updatedConversations);
      if (remainingIds.length > 0) {
        setActiveConversationId(remainingIds[0]);
      } else {
        if (isIncognitoChat) {
          setIncognitoMode(false);
        }
        startNewChat();
      }
    }
  };

  // Submit feedback on a message
  const submitFeedback = async (messageIndexOrQueryId, rating) => {
    const isQueryId = typeof messageIndexOrQueryId === 'string';
    
    let message;
    let query_id;
    
    if (isQueryId) {
      // Got query_id directly
      query_id = messageIndexOrQueryId;
      const conversation = conversations[activeConversationId];
      if (!conversation || !Array.isArray(conversation.messages)) {
        console.error("Cannot submit feedback: Invalid conversation");
        return;
      }
      
      message = conversation.messages.find(msg => msg.query_id === query_id);
      if (!message) {
        message = { sender: 'bot', query_id };
      }
    } else {
      // Got an index
      const messageIndex = messageIndexOrQueryId;
      const conversation = conversations[activeConversationId];
      if (!conversation || !Array.isArray(conversation.messages)) {
        console.error("Cannot submit feedback: Invalid conversation");
        return;
      }
      
      message = conversation.messages[messageIndex];
      if (!message) {
        console.error(`Cannot submit feedback: Invalid message index ${messageIndex}`);
        return;
      }
      
      query_id = message.query_id;
      if (!query_id) {
        console.error(`Message at index ${messageIndex} has no query_id`);
        return;
      }
    }
    
    // Update UI state immediately
    setActiveFeedback(prev => ({ ...prev, [query_id]: rating }));
    
    // Update persistent state
    setConversations(prev => {
      const updated = { ...prev };
      if (!updated[activeConversationId].feedback) {
        updated[activeConversationId].feedback = {};
      }
      updated[activeConversationId].feedback[query_id] = rating;
      return updated;
    });

    // Skip API if incognito
    if (incognitoMode) {
      return;
    }

    // Make API call to save feedback
    try {
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query_id: query_id,
          rating: rating,
          userId: userId,
          chatId: activeConversationId
        })
      });
      
      if (!response.ok) {
        console.error(`Feedback API call failed: ${response.status}`);
      }
    } catch (error) {
      console.error("Error submitting feedback to server:", error);
    }
  };

  // Copy text to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        // Temporary notification
        const copiedEl = document.createElement('div');
        copiedEl.className = 'copy-notification';
        copiedEl.innerText = 'Copied!';
        document.body.appendChild(copiedEl);
        
        setTimeout(() => {
          document.body.removeChild(copiedEl);
        }, 2000);
      })
      .catch(err => {
        console.error('Could not copy text: ', err);
      });
  };
  
  // Get feedback for a message
  const getFeedbackForMessage = useCallback((query_id) => {
    if (!query_id) return null;
    
    // Check activeFeedback state first
    if (activeFeedback && query_id in activeFeedback) {
      return activeFeedback[query_id];
    }
    
    // Then check persistent state
    if (activeConversation?.feedback && query_id in activeConversation.feedback) {
      return activeConversation.feedback[query_id];
    }
    
    return null;
  }, [activeConversation, activeFeedback]);

  // Group conversations by date
  function getConversationGroups() {
    const todayConversations = [];
    const previousConversations = [];

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    Object.values(conversations || {}).forEach(conv => {
      if (!conv || !Array.isArray(conv.messages) || conv.messages.length === 0) return;
      if ((incognitoMode && !conv.isIncognito) || (!incognitoMode && conv.isIncognito)) {
        return;
      }

      const lastMessage = conv.messages[conv.messages.length - 1];
      const lastMessageDate = new Date(lastMessage.timestamp || conv.date);

      if (lastMessageDate >= today) {
        todayConversations.push(conv);
      } else {
        previousConversations.push(conv);
      }
    });

    // Sort by latest (newest first)
    const sortByLatest = (a, b) => {
      const timeA = new Date(a.messages[a.messages.length - 1]?.timestamp || a.date);
      const timeB = new Date(b.messages[b.messages.length - 1]?.timestamp || b.date);
      return timeB - timeA;
    };

    todayConversations.sort(sortByLatest);
    previousConversations.sort(sortByLatest);

    return { todayConversations, previousConversations };
  }

  // Filter out hidden messages
  const visibleMessages = activeConversation?.messages ? 
    activeConversation.messages.filter(
      message => message.sender !== 'bot' || message.showInitialMessage !== false
    ) : [];

  const { todayConversations, previousConversations } = getConversationGroups();

  return (
    <div className="app">
      {/* Modal components */}
      {showIntroModal && <IntroModal onClose={() => setShowIntroModal(false)} />}
	  {showHelpModal && (
		  <HelpModal 
			onClose={() => setShowHelpModal(false)} 
			onFeedbackClick={() => {
			  setShowHelpModal(false);
			  setShowFeedbackModal(true);
			}}
		  />
	   )}
	  {showFeedbackModal && <FeedbackModal onClose={() => setShowFeedbackModal(false)} />}
      
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={startNewChat}>
            <MessageSquare size={16} />
            <span>New Chat</span>
          </button>
          <button className="toggle-btn" onClick={toggleSidebar}>
            <ChevronRight size={16} />
          </button>
        </div>
        
        <div className="conversation-list">
          {incognitoMode && (
            <div className="incognito-indicator">
              <EyeOff size={12} />
              <span>Incognito Mode - Conversations won't be saved</span>
            </div>
          )}
          
          {todayConversations.length > 0 && (
            <>
              <div className="conversation-header">Today</div>
              {todayConversations.map(conv => (
                <div 
                  key={conv.id} 
                  className={`conversation-item ${activeConversationId === conv.id ? 'active' : ''}`}
                  onClick={() => selectConversation(conv.id)}
                >
                  <MessageSquare size={14} className="conversation-icon" />
                  <span>{conv.title}</span>
                  <button 
                    className="delete-conv-btn"
                    onClick={(e) => deleteConversation(conv.id, e)}
                    aria-label="Delete conversation"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </>
          )}
          
          {previousConversations.length > 0 && (
            <>
              <div className="conversation-header">Previous 7 Days</div>
              {previousConversations.map(conv => (
                <div 
                  key={conv.id} 
                  className={`conversation-item ${activeConversationId === conv.id ? 'active' : ''}`}
                  onClick={() => selectConversation(conv.id)}
                >
                  <MessageSquare size={14} className="conversation-icon" />
                  <span>{conv.title}</span>
                  <button 
                    className="delete-conv-btn"
                    onClick={(e) => deleteConversation(conv.id, e)}
                    aria-label="Delete conversation"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </>
          )}
        </div>
      </div>

      {/* Main content */}
      <div className={`main-content ${sidebarOpen ? '' : 'expanded'}`}>
        <header className="main-header">
          {/* Left-side (namespace display) */} 
		  <div className="header-left">
			  {!sidebarOpen && (
				<button className="menu-btn" onClick={toggleSidebar} aria-label="Toggle sidebar">
				  <MessageSquare size={20} />
				</button>
			  )}
			  
			  <div className="status-indicators">  
			  {namespace !== 'default' && (
				  <div className="namespace-status">
					<span className="desktop-only">
					  Search Space: <strong>{namespaceLabels[namespace]}</strong>
					</span>
					<span className="mobile-only">
					  <strong>{namespace === 'course' ? 'Course Offerings' : namespace === 'classroom' ? 'Study Spot Finder' : ''}</strong>
					</span>
					{namespaceUpdateInfo[namespace] && (
					  <div className="namespace-update-info">
						<span className="desktop-only">{namespaceUpdateInfo[namespace].desktop}</span>
						<span className="mobile-only">{namespaceUpdateInfo[namespace].mobile}</span>
					  </div>
					)}
				  </div>
			  )}
			
			  {deepSearchMode && (
				  <div className="deep-search-badge deep-search-only">
					  <Radar size={15} className="deep-search-icon" />
					  <span>Deep Research Active</span>
				  </div>
			  )}

			  </div>
		  </div>
          {/* Center with logo and title */}
          <div className="header-center">
            <img src="/logo_new.png" alt="askNEU logo" className="neu-logo" />
          </div>

          {/* Right-side icons with Help button */}
          <div className="header-right">
            <button
              className="help-btn"
              onClick={() => setShowHelpModal(true)}
              title="Help & Information"
              aria-label="Help and Information"
            >
              <HelpCircle size={18} />
            </button>
            <button
              className={`mode-toggle ${incognitoMode ? 'active' : ''}`}
              onClick={toggleIncognitoMode}
              title={incognitoMode ? "Turn Off Incognito Mode" : "Turn On Incognito Mode"}
              aria-label={incognitoMode ? "Turn Off Incognito Mode" : "Turn On Incognito Mode"}
            >
              {incognitoMode ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
            <button
              className="theme-toggle"
              onClick={toggleDarkMode}
              title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
              aria-label={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
            >
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <div className="user-menu">
              <img
                src={user?.picture || `https://ui-avatars.com/api/?name=${user?.name || 'G'}&background=cc0000&color=fff`}
                alt="User Avatar"
                className="user-avatar"
                onClick={() => setShowMenu(!showMenu)}
              />
              {showMenu && (
                <div className="user-dropdown">
                  <div className="user-name">{user?.name || 'Guest'}</div>
                  <button onClick={user?.email === 'guest@askneu.ai' ? () => {
                    sessionStorage.removeItem('user');
                    window.location.reload();
                  } : handleLogout}>
                    {user?.email === 'guest@askneu.ai' ? 'Login' : 'Logout'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>		
        <div className="chat-container">
        {activeConversation && activeConversation.messages && 
         activeConversation.messages.length === 1 && 
         activeConversation.messages[0].sender === 'bot' ? (
          <div className="welcome-screen">
            <div className="neu-logo-large">
              <img src="/logo.png" alt="NEU Logo" />
            </div>
            <h2>Hi! I am Northeastern University Assistant. What can I help with?</h2>
            
            <div className="suggested-questions-grid">
              {getSuggestedQuestions().map((question, index) => (
                <button 
                  key={index}
                  className="suggested-question"
                  onClick={() => handleSuggestedQuestion(question)}
                >
                  <MessageSquare size={18} className="suggested-question-icon" />
                  <span>{question}</span>
                </button>
              ))}
            </div>
            
            <div className="namespace-options">
              <button
                className={`namespace-option ${namespace === 'course' ? 'active' : ''}`}
                onClick={() => handleSpecialAction('course')}
              >
                <div className="namespace-icon">
                  <BookOpen 
                    size={18} 
                    style={{color: namespace === 'course' ? 'white' : '#cc0000'}}/>
                </div>
                <div className="namespace-info">
                  <span>Course Offerings</span>
                </div>
              </button>

              <button
                className={`namespace-option ${namespace === 'classroom' ? 'active' : ''}`}
                onClick={() => handleSpecialAction('classroom')}
              >
                <div className="namespace-icon">
                  <School
                    size={18} 
                    style={{color: namespace === 'classroom' ? 'white' : '#cc0000'}}/>
                </div>
                <div className="namespace-info">
                  <span>Study Spot Finder</span>
                </div>
              </button>
            </div>
          </div>
        ) : (
          <div className="messages">
              {visibleMessages.map((message, index) => (
                <MessageComponent
                  key={`${message.query_id || `msg_${index}_${message.timestamp}`}`}
                  message={message}
                  index={index}
                  setConversations={setConversations}
                  conversations={conversations}
                  activeConversationId={activeConversationId}
                  submitFeedback={submitFeedback}
                  copyToClipboard={copyToClipboard}
                  getFeedbackForMessage={getFeedbackForMessage}
                  activeFeedback={activeFeedback}
                  activeConversation={activeConversation}
                  setActiveFeedback={setActiveFeedback}
                />
              ))}
              
              {/* Loading indicator */}
              {isLoading && activeConversation && (
                <div className="message bot">
                  <div className="message-container">
                    <div className="message-content">
                      <div className="message-header">
                        <div className="message-sender">NEU Assistant</div>
                      </div>
                      <div className="message-text">
                        <div className="typing-indicator">
                          <div className="typing-dot"></div>
                          <div className="typing-dot"></div>
                          <div className="typing-dot"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
        
        {/* Input area */}
        <div className="input-area">
          <div className="input-container-wrapper">
            <div className="input-container">
            
              {/* Namespace icons */}
              {!(activeConversation && 
                 activeConversation.messages && 
                 activeConversation.messages.length === 1 && 
                 activeConversation.messages[0].sender === 'bot') && (
                <div className="namespace-floating-buttons">
                  <button
                    className={`namespace-icon-btn course ${namespace === 'course' ? 'active' : ''}`}
                    onClick={() => setNamespace(namespace === 'course' ? 'default' : 'course')}
                    title="Course Offerings"
                  >
                    <BookOpen size={16} />
                  </button>

                  <button
                    className={`namespace-icon-btn classroom ${namespace === 'classroom' ? 'active' : ''}`}
                    onClick={() => setNamespace(namespace === 'classroom' ? 'default' : 'classroom')}
                    title="Study Spot Finder"
                  >
                    <School size={16} />
                  </button>
                </div>
              )}
              <textarea 
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder={getPlaceholderText()}
                rows="1"
              />              
              {/* Deep search toggle */}
              <div className="search-tools">
                <button 
                  className={`deepsearch-btn ${deepSearchMode ? 'active' : ''}`}
                  onClick={toggleDeepSearch}
                  title={deepSearchMode ? "Disable DeepSearch" : "Enable DeepSearch"}
                >
                  DeepSearch
                </button>
              </div>
              
              {/* Send button */}
              <div className="input-buttons">
                <button 
                  className="send-btn"
                  onClick={sendMessage}
                  disabled={isLoading || input.trim() === ''}
                  aria-label="Send message"
                >
                  <Send size={16} color="white" />
                </button>
              </div>
            </div>
            
            <div className="footer">
              <span>Your Campus Companion - Built by Huskies, For Huskies</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;