const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const mongoose = require('mongoose');
const axios = require('axios');

// Import models
const User = require('./models/User');
const Feedback = require('./models/Feedback');
const Conversation = require('./models/Conversation');
const AppFeedback = require('./models/AppFeedback');


// Import routes
const conversationRoutes = require('./routes/Conversation');

dotenv.config();

const app = express();
const port = process.env.PORT || 8080;
const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://localhost:5001/query';
const PYTHON_FEEDBACK_URL = process.env.PYTHON_FEEDBACK_URL || 'http://localhost:5001/feedback';

// Connect to MongoDB
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log("✅ Connected to MongoDB"))
  .catch(err => console.error("❌ MongoDB connection error:", err));

app.use(cors());
app.use(express.json());
app.use((req, res, next) => {
  res.setHeader('Cross-Origin-Opener-Policy', 'same-origin-allow-popups');
  next();
});

// Use the conversation routes
app.use('/api/conversations', conversationRoutes);

// Chat endpoint
app.post('/api/chat', async (req, res) => {
  const { query, namespace = "default", search_mode = "direct", userId } = req.body;

  try {
    console.log("🔁 Incoming Query:", { query, namespace, search_mode });

    const response = await axios.post(PYTHON_SERVICE_URL, {
      query,
      namespace,
      search_mode
    });

    const { answer, sources, processing_time, search_mode: returnedSearchMode, query_id } = response.data;
    console.log("✅ Response with query_id:", query_id);
    
    res.json({
      answer: answer || "⚠️ No proper answer returned.",
      sources: sources || [],
      query_id: query_id,
      processing_time: processing_time || 0,
      search_mode: returnedSearchMode || search_mode
    });
  } catch (err) {
    console.error("❌ Error forwarding to Python:", err.message);
    res.status(500).json({
      answer: "❌ Internal server error while fetching response from Python.",
      error: err.message
    });
  }
});

// User check/creation endpoint
app.post('/api/users/check', async (req, res) => {
  try {
    const { email, googleId } = req.body;
    
    // Find by email
    let user = await User.findOne({ email });
    
    if (user) {
      // User exists - return their ID
      return res.json({ 
        userId: user.userId,
        exists: true 
      });
    } else {
      // New user - create a new ID
      const userId = `google_${googleId}`;
      
      // Create new user
      const newUser = new User({
        userId,
        email,
        authProvider: 'google',
        lastLogin: new Date()
      });
      
      await newUser.save();
      
      return res.json({ 
        userId,
        exists: false 
      });
    }
  } catch (error) {
    console.error('Error checking user:', error);
    res.status(500).json({ error: 'Failed to check user' });
  }
});

app.post('/api/app-feedback/submit', async (req, res) => {
  try {
    const { name, email, feedback, rating, timestamp } = req.body;
    const userId = req.body.userId || req.headers['x-user-id'] || 'anonymous';
    
    // Check for required fields
    if (!name) {
      return res.status(400).json({ error: 'Name is required' });
    }
    
    if (!email) {
      return res.status(400).json({ error: 'Email is required' });
    }
    
    if (!feedback) {
      return res.status(400).json({ error: 'Feedback text is required' });
    }
    
    // Simple email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ error: 'Invalid email format' });
    }
    
    // Create new feedback entry
    const appFeedback = new AppFeedback({
      name,
      email,
      feedback,
      rating: rating || 0,
      timestamp: timestamp || new Date(),
      userId
    });
    
    await appFeedback.save();
    
    console.log('📝 App feedback saved:', { name, email, rating });
    
    return res.status(200).json({ success: true, message: 'App feedback submitted successfully' });
  } catch (error) {
    console.error('❌ Error saving app feedback:', error);
    return res.status(500).json({ error: 'Failed to save app feedback' });
  }
});


// Feedback endpoint
app.post('/api/feedback', async (req, res) => {
  const query_id = req.body.query_id || req.body.queryId;
  const rating = req.body.rating;
  const userId = req.body.userId || 'anonymous';
  const chatId = req.body.chatId || req.body.activeConversationId || 'unknown';
  
  console.log('📬 Received feedback:', { query_id, rating, userId, chatId });
  
  if (!query_id || !rating) {
    return res.status(400).json({ error: 'Missing query ID or rating' });
  }

  try {
    // Save to Feedback collection
    const feedback = await Feedback.create({ 
      userId, 
      chatId, 
      queryId: query_id, 
      rating, 
      timestamp: new Date() 
    });
    
    // Update conversation feedback
    const conversation = await Conversation.findOne({ 'messages.query_id': query_id });
    
    if (conversation) {
      if (!conversation.feedback) {
        conversation.feedback = {};
      }
      conversation.feedback[query_id] = rating;
      await conversation.save();
    }

    return res.status(200).json({ message: 'Feedback saved successfully' });
  } catch (err) {
    console.error('❌ Error saving feedback:', err);
    return res.status(500).json({ error: 'Failed to save feedback' });
  }
});

// Delete conversation with feedback cleanup
app.delete('/api/conversations/delete', async (req, res) => {
  const { userId, conversationId } = req.body;

  if (!conversationId) {
    return res.status(400).json({ error: "conversationId is required" });
  }

  try {
    await Conversation.deleteOne({ id: conversationId });
    await Feedback.deleteMany({ chatId: conversationId });

    res.json({ success: true });
  } catch (err) {
    console.error("❌ Error deleting conversation:", err);
    res.status(500).json({ error: "Failed to delete conversation" });
  }
});


// Guest user registration endpoint NEW
app.post('/api/users/guest', async (req, res) => {
  try {
    const { guestId, timestamp } = req.body;
    
    if (!guestId) {
      return res.status(400).json({ error: 'Missing guestId' });
    }
    
    // Check if this guest already exists
    const existingUser = await User.findOne({ userId: guestId });
    
    if (existingUser) {
      // Update last login time
      existingUser.lastLogin = new Date();
      await existingUser.save();
      
      return res.json({ success: true, exists: true });
    }
    
    // Create new guest user
    const newUser = new User({
      userId: guestId,
      email: `${guestId}@guest.askneu.ai`, // Placeholder email
      authProvider: 'guest',
      lastLogin: new Date(),
      createdAt: timestamp ? new Date(timestamp) : new Date()
    });
    
    await newUser.save();
    
    res.json({ success: true, exists: false });
  } catch (error) {
    res.status(500).json({ error: 'Failed to register guest user' });
  }
});


// Start server
const http = require('http');
const server = http.createServer(app);

server.on('error', (error) => {
  if (error.code === 'EADDRINUSE') {
    console.error(`⚠️ Port ${port} is already in use. Trying port ${port + 1}`);
    app.listen(port + 1, () => {
      console.log(`Server running at http://localhost:${port + 1}`);
    });
  } else {
    console.error('❌ Server error:', error);
  }
});

server.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});