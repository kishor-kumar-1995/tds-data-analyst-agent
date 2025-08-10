# TDS Data Analyst Agent

This is a FastAPI-based Data Analyst Agent that accepts a file containing analysis questions, calls an LLM API (OpenAI or AI Pipe), performs scraping and data analysis, and returns JSON answers and charts as base64 images.

## Features

- Upload a questions file via `/api/` endpoint
- Uses FastAPI for backend API
- Scrapes Wikipedia and performs data analysis using pandas, numpy, and matplotlib
- Calls OpenAI or AI Pipe API to generate answers
- Returns results in JSON format with embedded charts as base64 data URIs

## Setup & Deployment

1. Install dependencies:
