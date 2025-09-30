# Multi-Agent Travel Planner - Comprehensive Requirements & Task List

## Project Overview

An AI Engineer Flight Booking Agentic product demonstrating multi-agent coordination using AutoGen. The system will showcase intelligent conversation flow between specialized agents for flight booking, hotel booking, and travel planning.

## System Architecture

- **Frontend**: React-based GUI (already created)
- **Backend**: AutoGen-based multi-agent system
- **APIs**: Flight and Hotel booking endpoints (already created)
- **Model Provider**: OpenAI API
- **Deployment**: Localhost demonstration

## Core User Flow

```
U (User): I want to go from Sri Lanka to Thailand
A1 (Conversational Agent): When do you want to go?
U (User): 26th November 2025
A1 (Conversational Agent): When are you planning to come back?
U (User): 12th December 2025 (return date)
A1 (Conversational Agent): Parses source & destination → calls flight API → lists available trips
U (User): Says it's a business trip and wants a hotel
A1 (Conversational Agent): Hands off to Hotel Booking Agent
U (User): Prefers 4-star instead of 5-star → agent adjusts
A2 (Flight Booking Agent): Asks for confirmation → after user confirms, flight is marked booked
A3 (Hotel Booking Agent): Fetches available hotels by city, asks user where to stay, finalizes booking
A4 (Planner Agent): Creates itinerary using web search results
```

## Current Implementation Status

### ✅ Completed with Convex

- **Database & APIs**: Fully functional Convex backend with 270 flights, 155 hotels across 10 Asian countries
- **Reference Data**: Countries, cities, and flight routes properly structured
- **Booking System**: Working flight and hotel booking with confirmation references
- **User Management**: User tracking by email with booking history
- **API Documentation**: Complete with examples in README.md

### 🔄 Next: AutoGen Integration

The focus now shifts to implementing the AutoGen multi-agent system that will interact with these existing APIs.

## Task Breakdown for AutoGen Implementation

### Phase 1: Data Infrastructure & API Development ✅ COMPLETED

#### 1.1 Flight Data Setup

- [x] **Create Flight Database**

  - [x] Generate 100+ flight bookings for next 3 months (starting October 2025)
  - [x] Focus on Asia region: 7-10 countries (Thailand, Malaysia, Singapore, Indonesia, Philippines, Vietnam, Cambodia, Japan, South Korea, India)
  - [x] Include realistic flight times, prices, and airline information
  - [x] Implement using Convex or alternative quick prototyping solution

- [x] **Flight API Endpoints**
  - [x] `GET /api/flights/search` - Search flights by source, destination, date
  - [x] `POST /api/flights/book` - Book a specific flight
  - [x] `GET /api/flights/booking/{id}` - Get booking details
  - [x] Document all endpoints with request/response schemas

#### 1.2 Hotel Data Setup

- [x] **Create Hotel Database**

  - [x] Add hotels in 3-4 Asian countries
  - [x] Multiple cities per country
  - [x] Include star ratings (3-star, 4-star, 5-star)
  - [x] Date ranges for availability
  - [x] Realistic pricing and amenities

- [x] **Hotel API Endpoints**
  - [x] `GET /api/hotels/search` - Search hotels by city, dates, star rating
  - [x] `POST /api/hotels/book` - Book a specific hotel
  - [x] `GET /api/hotels/booking/{id}` - Get booking details (via user bookings endpoint)
  - [x] Document all endpoints with request/response schemas

### Phase 2: AutoGen Multi-Agent System

#### 2.1 Agent Architecture Design

- [ ] **Define Agent Roles**

  - [ ] **Conversational Agent (A1)**: Main coordinator, handles initial conversation
  - [ ] **Flight Booking Agent (A2)**: Specializes in flight search and booking
  - [ ] **Hotel Booking Agent (A3)**: Specializes in hotel search and booking
  - [ ] **Planner Agent (A4)**: Creates travel itineraries using web search

- [ ] **Agent Capabilities**
  - [ ] Each agent should have access to relevant API endpoints
  - [ ] Agents should be able to hand off conversations appropriately
  - [ ] Implement memory/context sharing between agents

#### 2.2 Conversation Flow Implementation

- [ ] **User Information Collection**

  - [ ] Collect user name and email (required for bookings)
  - [ ] Store as primary identifiers for booking entries

- [ ] **Flight Booking Flow**

  - [ ] Parse source and destination from natural language
  - [ ] Handle date parsing and validation
  - [ ] Present flight options to user
  - [ ] Confirm booking and simulate payment process

- [ ] **Hotel Booking Flow**

  - [ ] Trigger based on user mentioning accommodation needs
  - [ ] Handle star rating preferences
  - [ ] Filter by destination city
  - [ ] Confirm booking details

- [ ] **Travel Planning**
  - [ ] Generate itinerary using web search results
  - [ ] Integrate flight and hotel bookings into plan

#### 2.3 AutoGen Configuration

- [ ] **Setup AutoGen Framework**
  - [ ] Configure agent definitions and roles
  - [ ] Implement conversation patterns and handoffs
  - [ ] Set up OpenAI API integration
  - [ ] Configure agent memory and context management

### Phase 3: Integration & Testing

#### 3.1 API Integration

- [ ] **Connect Agents to APIs**
  - [ ] Implement API calling functions for each agent
  - [ ] Handle API errors and edge cases
  - [ ] Add logging for debugging

#### 3.2 Terminal-Based Interface

- [ ] **Command Line Interface**
  - [ ] Create main entry point for agent interaction
  - [ ] Implement conversation loop
  - [ ] Add proper error handling and user guidance

#### 3.3 Frontend Integration (Future Enhancement)

- [ ] **WebSocket Connection (Time Permitting)**
  - [ ] Connect React frontend to AutoGen backend
  - [ ] Real-time conversation display
  - [ ] Chat interface for agent interaction

### Phase 4: Documentation & Demo Preparation

#### 4.1 Documentation

- [x] **API Documentation**

  - [x] Complete API documentation in README.md
  - [x] Include example requests and responses
  - [x] Add authentication details (currently no auth required for demo)

- [ ] **Setup Instructions**
  - [ ] Step-by-step installation guide
  - [ ] Environment configuration
  - [ ] Database setup instructions

#### 4.2 Demo Scenarios

- [ ] **Test Scenarios**
  - [ ] Single destination booking (Sri Lanka → Thailand)
  - [ ] Business trip with hotel requirements
  - [ ] Star rating preferences
  - [ ] Complete booking flow demonstration

## Technical Constraints & Notes

### System Limitations

- **Single Source + Single Destination**: No multi-country booking support
- **Payment Simulation**: No actual payment processing - inform users that payment link would be sent via email
- **Region Focus**: Asia-Pacific countries only
- **Demo Environment**: Localhost deployment for student demonstrations

### Data Requirements ✅ COMPLETED

- **Flight Data**: 270 flights covering 10 Asian countries ✅
- **Hotel Data**: 155 hotels across multiple cities in 10 countries ✅
- **Date Ranges**: Proper availability windows implemented ✅
- **Reference Data**: 20 cities, country mappings, airport codes ✅

### Technical Stack

- **Backend**: Python with AutoGen framework (to be implemented)
- **APIs**: RESTful endpoints using Convex ✅ COMPLETED
- **Model**: OpenAI API for language processing
- **Database**: Convex (fully implemented with 270 flights, 155 hotels) ✅ COMPLETED

## Success Criteria

1. **Functional Multi-Agent System**: Agents successfully coordinate and hand off conversations
2. **Complete Booking Flow**: Users can book both flights and hotels through agent interaction
3. **Natural Language Processing**: Agents understand and respond to user intent appropriately
4. **Data Persistence**: Bookings are recorded with user information
5. **Demo Ready**: System runs reliably on localhost for student demonstrations

## Next Steps for Developer

1. Review existing frontend implementation in `/frontend` directory
2. Set up AutoGen development environment
3. Begin with Phase 1 data infrastructure
4. Implement agents incrementally, testing each phase
5. Focus on terminal-based interaction first
6. Prepare demo scenarios for October sessions

---

**Note**: Frontend is already implemented. Focus should be on AutoGen backend system and API development to complete the agentic pipeline.
