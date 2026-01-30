---
name: hybrid-mvp-architect
description: Use when architecting a new product or feature from a user's scenario. It balances a minimal core feature (MVP) with production-ready, commercial-grade essential infrastructure (Auth, Security, Data Persistence).
---

# Hybrid MVP Architect

## Overview

**Hybrid MVP Architecture is the discipline of innovating fast on the core while building on rock-solid commercial foundations.**

The goal is to produce an implementation plan that validates the "Minimum Viable Product" (MVP) core without compromising on the "Commercial Minimum" necessities.

## The Hybrid Strategy

This skill is **technology-agnostic**. Whether building a Web App, Mobile App, or AI Tool, the strategy remains:

| Component Category | Strategy | Implementation Level |
| :--- | :--- | :--- |
| **Core Value Proposition** | **MVP (Minimalist)** | **Experimental**: Fast, raw, no-frills code that proves the idea works. |
| **Supporting Infrastructure** | **Commercial Grade** | **Production-Ready**: Secure Auth, Persistent DB, Error Monitoring, Scalable Hosting. |

## When to Use

- Starting a new SaaS or application from a vague requirement.
- Adding a major new feature that requires its own infrastructure.
- Converting a "prototype" idea into a "ready-to-launch" plan.
- When the user asks for a "Minimal Viable Product" or "MVP" but expects commercial quality.

## Core Pattern: Requirement Distillation

## Implementation Workflow

### Step 1: Commitment Announcement
You MUST announce: *"I am applying the Hybrid MVP Architect strategy. Core features will be minimal; essential infrastructure will be commercial-grade."*

### Step 2: Tech Stack Selection
Prefer established, robust tools that offer "commercial-grade out of the box" (e.g., Supabase, Clerk, Stripe).

### Step 3: Blueprint Generation
Follow the template below.

## Blueprint Generation Template

When triggered, you MUST output the solution in this specific format:

### 1. Product Vision & MVP Scope
- **Core Problem**: [What problem are we solving?]
- **The "Magic" Moment**: [What is the one feature that proves value?]

### 2. The MVP Core (The "Cheap" Part)
- **Logic**: Simple scripts/functions. No complex abstractions.
- **UI**: Functional, using standard components. Focus on flow, not polish.
- **Goal**: Ship in days, not weeks.

### 3. Commercial Foundation (The "Solid" Part)
- **Authentication**: [Specific production-grade solution, e.g., Supabase Auth with OAuth/JWT]
- **Data Persistence**: [Relational DB schema, migration strategy]
- **Security**: [HTTPS, Input validation, Environment variables]
- **Error Handling**: [Global error boundaries, logging/monitoring setup]

### 4. Implementation Checklist
- [ ] Setup Production Infrastructure (Auth, DB)
- [ ] Implement Core MVP Logic
- [ ] Connect Core to Auth/DB
- [ ] Basic Production Readiness Check (Security, Errors)

## Technology Selection Guide (Commercial Standards)

Always recommend "Commercial Grade" defaults for supporting infrastructure:
- **Identity**: Supabase Auth, Clerk, Auth0, Firebase Auth (No custom/mock auth).
- **Example**: Use Supabase for Auth to get Email/Password + Social OAuth + MFA in minutes.
- **Persistence**: PostgreSQL, MongoDB Atlas, Supabase (No local-only storage).
- **Reliability**: Sentry (Error tracking), Logtail (Logging).
- **Compliance**: Terms/Privacy templates, basic GDPR consideration.

## Common Mistakes (Rationalization Table)

| Excuse | Reality |
| :--- | :--- |
| "I'll add Auth later, let's use a mock." | **NO.** A product without Auth is a demo, not an MVP. Use a commercial provider. |
| "Let's use a complex design system for the core." | **NO.** Keep the core UI raw. Focus tokens on functionality. |
| "Simple code means no error handling." | **NO.** MVP core should be simple, but the *application* must be robust. |

## Red Flags - STOP and Start Over

- Hardcoded credentials or mock authentication.
- Core features that include complex "what if" abstractions.
- Lack of environment variable management for sensitive keys.
- Data persistence using only `localStorage` for a SaaS idea.

**REQUIRED BACKGROUND:** You MUST understand [writing-skills](file:///e:/Files/PycharmProjects/test/.trae/skills/writing-skills/SKILL.md) and [production-readiness-checklist](file:///e:/Files/PycharmProjects/test/.trae/skills/production-readiness-checklist/SKILL.md).
