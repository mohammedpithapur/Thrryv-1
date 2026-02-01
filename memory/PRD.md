# Thrryv - Evidence-Based Truth Platform

## Original Problem Statement
Build "Thrryv", a full-stack web app where users can post short, immutable claims (up to 250 words) with a domain and confidence level. Users can upload supporting media (text, images, short videos). The community adds annotations (supporting/contradicting evidence or context), which can also include media. 

Key Requirements:
- Automatically label uploaded AI-generated media as "AI-generated"
- Calculate a reputation score for users based on contribution value and accuracy
- Display truth labels (True, False, Likely False, Uncertain) and credibility scores
- Clean, neutral UI with feed surfacing recent, debated, and uncertain claims

## Tech Stack
- **Frontend**: React, Tailwind CSS, Shadcn UI components
- **Backend**: FastAPI (Python), MongoDB with Motor async driver
- **Authentication**: JWT-based
- **AI**: Rule-based fact-checking and domain classification (in server.py)

## Core Features Implemented ✅

### Authentication
- User registration with email/username/password
- Login/logout with JWT tokens
- Protected routes and API endpoints

### Claims System
- Create claims with text, confidence level
- AI-powered domain classification (Science, Health, History, Politics, etc.)
- AI-powered truth label assignment (True, False, Likely False, Uncertain)
- Media attachment support (images, videos)

### Feed
- Three tabs: Recent, Debated, Uncertain
- Real-time claim counts per tab
- Pagination support
- Truth badges and credibility scores on cards

### Annotations
- Three types: Support, Contradict, Context
- Media upload for evidence
- Voting system (helpful/not helpful)
- Author attribution with reputation

### User Features
- Profile page with stats (claims, annotations, helpful votes)
- Settings page with:
  - Profile picture upload
  - Username change
  - Password change
  - Dark/Light mode toggle (fully functional)

### Dark Mode
- Full dark mode support via ThemeContext
- Persists in localStorage
- Affects all pages and components

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT
- `GET /api/auth/me` - Get current user

### Claims
- `GET /api/claims` - List claims (with tab filtering)
- `POST /api/claims` - Create claim (with AI processing)
- `GET /api/claims/{id}` - Get claim details
- `GET /api/claims/{id}/annotations` - Get claim annotations
- `POST /api/claims/{id}/annotations` - Add annotation

### Annotations
- `POST /api/annotations/{id}/vote?helpful=true/false` - Vote on annotation

### Users
- `GET /api/users/{id}` - Get user profile
- `PATCH /api/users/settings` - Update settings
- `POST /api/users/profile-picture` - Upload profile picture

### Media
- `POST /api/media/upload` - Upload media file
- `GET /api/media/{id}` - Get media file

## Database Schema

### Users Collection
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "password": "hashed",
  "reputation_score": "float",
  "profile_picture_url": "string|null",
  "contribution_stats": {
    "claims_posted": "int",
    "annotations_added": "int",
    "helpful_votes_received": "int"
  },
  "created_at": "datetime"
}
```

### Claims Collection
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "text": "string",
  "domain": "string (AI-assigned)",
  "confidence_level": "int",
  "media_ids": ["uuid"],
  "truth_label": "string (AI-assigned)",
  "credibility_score": "float",
  "created_at": "datetime"
}
```

### Annotations Collection
```json
{
  "id": "uuid",
  "claim_id": "uuid",
  "user_id": "uuid",
  "annotation_type": "support|contradict|context",
  "text": "string",
  "media_ids": ["uuid"],
  "helpful_votes": "int",
  "not_helpful_votes": "int",
  "created_at": "datetime"
}
```

## Configuration

### Frontend .env
```
REACT_APP_BACKEND_URL=<preview-url>
WDS_SOCKET_PORT=443
DISABLE_VISUAL_EDITS=true
```

### Backend .env
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
JWT_SECRET=<secret>
CORS_ORIGINS=*
```

## Test Credentials
- Email: testuser_e1@test.com
- Password: testpassword123

## Completed - January 31, 2026
- ✅ Fixed recurring Babel metadata plugin build error (DISABLE_VISUAL_EDITS=true)
- ✅ Implemented dark/light mode with ThemeContext
- ✅ Fixed annotation voting (query param vs body issue)
- ✅ All core features tested and working (100% pass rate)

## Completed - February 1, 2026
- ✅ **AI Baseline Reputation Evaluator** - Implemented GPT-5.2 powered content evaluation
  - Evaluates claims at publish time for: clarity, originality, relevance, effort, evidentiary value
  - Awards reputation boosts (+5 to +15 points) for high-quality contributions
  - Never penalizes low-value content (non-punitive)
  - Separate from community annotation system
  - Shows evaluation results with detailed scores in modal after submission
  - For media posts: evaluates if images/videos add meaningful information vs decoration

- ✅ **Delete Account Feature**
  - Delete Account option in Settings page under "Danger Zone"
  - Confirmation modal requires typing "Delete Account" exactly
  - Hard deletes all user data: account, claims, annotations, notifications

- ✅ **Delete Post Feature**
  - Delete option on claims (from feed and profile page)
  - Reverses reputation boost when claim is deleted
  - Updates user stats after deletion

- ✅ **Mobile Layout Fix**
  - Floating Action Button (FAB) for "New Claim" on mobile devices
  - Responsive navbar with hamburger menu for mobile
  - Bell icon for notifications accessible on mobile

- ✅ **Notification System**
  - Bell icon in header shows unread count
  - Dedicated Notifications page (/notifications)
  - Notifications triggered when someone annotates user's claims
  - Mark as read / Mark all as read functionality

- ✅ **Profile Page Updates**
  - Expandable/collapsible Claims and Annotations sections
  - Shows all user's claims with reputation boost displayed
  - Delete option on own claims from profile
  - Click to navigate to claim detail

- ✅ **Feed Updates**
  - Reputation boost visible on posts (+X.X in green)
  - Delete menu option for own posts
  - Responsive design for mobile

- ✅ **Welcome Page Update**
  - Headline: "Where Your Reputation Matters"
  - Subtext: "A transparent social media platform..."

- ✅ **Strict 250-Word Limit**
  - Word count display on create claim page
  - Exceeds limit warning
  - Submit button disabled when over limit

- ✅ **Improved AI Domain Classification** (Updated)
  - Uses GPT-5.2 for intelligent domain classification
  - Analyzes text AND media content for context
  - 15 domain categories: Science, Health, Technology, Politics, Economics, Environment, History, Society, Sports, Entertainment, Education, Geography, Food, Law, Religion
  - Provides confidence score and reasoning
  - No more "Other" fallback category

- ✅ **Congratulatory Modal with Clear Reasoning**
  - Shows for ALL claims after submission (not just high-quality)
  - Displays AI-classified domain and truth label
  - Shows quality scores (Clarity, Originality, Relevance, Effort, Evidence Value)
  - Explains why reputation was/wasn't awarded
  - "OK, View My Claim" button to dismiss

## Backlog / Future Tasks

### P1 - High Priority
- Implement Hive AI integration for AI-generated media detection
- Video thumbnails on feed (currently using poster attribute or fallback)
- Profile settings end-to-end testing (username/password change)

### P2 - Medium Priority
- Interactive tutorial for first-time users
- Video autoplay verification with real video files
- Refactor rule-based AI fact-checker to data-driven structure
- Add media analysis to annotations (not just claims)

### P3 - Low Priority
- Enhanced credibility algorithm
- User notifications system
- Claim sharing functionality
- Leaderboard for top contributors
