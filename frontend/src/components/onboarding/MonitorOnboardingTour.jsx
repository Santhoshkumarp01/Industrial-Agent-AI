/**
 * MonitorOnboardingTour - First-time user guided walkthrough for Live Monitor Intelligence
 * 
 * Separate tour for monitoring panel explaining Demo Anomaly and agent analysis
 */
import React, { useState, useEffect } from 'react'

const ONBOARDING_KEY = 'industrial_agent_monitor_onboarding_complete'

const MONITOR_STEPS = [
  {
    id: 'welcome',
    title: 'Welcome to Live Monitor Intelligence! 📡',
    message: 'Real-time equipment monitoring with AI-powered diagnostics. Our 3-agent system analyzes sensor data, predicts failures, and provides maintenance recommendations.',
    highlight: null,
    position: 'center',
    actions: ['Skip Tour', 'Start Tour →']
  },
  {
    id: 'equipment-cards',
    title: 'Step 1: Monitor Equipment Status',
    message: 'Each card shows real-time sensor readings (vibration, temperature, current, pressure) and current fault status. Click any card to view detailed sensor trends.',
    tip: '💡 Color-coded status: 🟢 Normal • 🟡 Warning • 🔴 Critical. Backend logs update every 5 seconds.',
    highlight: null,
    position: 'center',
    actions: ['← Back', 'Skip', 'Next →']
  },
  {
    id: 'demo-anomaly',
    title: 'Step 2: Try Demo Anomaly',
    message: 'Click "DEMO ANOMALY" to inject a test vibration fault on the General Industrial Motor. This triggers our 3-agent system for full diagnostic analysis.',
    tip: '💡 The system will run: Agent 1 (Root Cause) → Agent 2 (Risk + RUL) → Agent 3 (Maintenance Plan). Results appear in the right panel.',
    highlight: '[data-tour="demo-anomaly"]',
    position: 'bottom-right',
    actions: ['← Back', 'Skip', 'Next →']
  },
  {
    id: 'agent-analysis',
    title: 'Step 3: Real-Time Agent Streaming',
    message: 'Watch the 3-agent system work: Root Cause Analysis → Risk Assessment with RUL prediction → Maintenance recommendations with spare parts lookup.',
    tip: '💡 All analysis is saved to the Operations Logbook and can be exported as PDF reports. Citations link back to equipment manuals.',
    highlight: null,
    position: 'center',
    actions: ['← Back', 'Skip', 'Next →']
  },
  {
    id: 'monitor-chat',
    title: 'Step 4: Monitor AI Chat',
    message: 'The right panel shows analysis results and maintains a separate chat history for monitoring. Ask follow-up questions about detected faults or equipment status.',
    tip: '💡 This chat is separate from Chat Assistant — it focuses on real-time monitoring and diagnostic results.',
    highlight: '[data-tour="monitor-chat"]',
    position: 'top-left',
    actions: ['← Back', 'Skip', 'Finish Tour ✓']
  }
]

export default function MonitorOnboardingTour({ onComplete }) {
  const [isActive, setIsActive] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [highlightedElement, setHighlightedElement] = useState(null)

  useEffect(() => {
    // Check if onboarding already completed
    const completed = localStorage.getItem(ONBOARDING_KEY)
    if (!completed) {
      // Show onboarding after a brief delay
      setTimeout(() => setIsActive(true), 1000)
    }
  }, [])

  useEffect(() => {
    if (isActive && MONITOR_STEPS[currentStep].highlight) {
      const selector = MONITOR_STEPS[currentStep].highlight
      const element = document.querySelector(selector)
      setHighlightedElement(element)
    } else {
      setHighlightedElement(null)
    }
  }, [isActive, currentStep])

  const handleNext = () => {
    if (currentStep < MONITOR_STEPS.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      completeTour()
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSkip = () => {
    completeTour()
  }

  const completeTour = () => {
    localStorage.setItem(ONBOARDING_KEY, 'true')
    setIsActive(false)
    if (onComplete) onComplete()
  }

  if (!isActive) return null

  const step = MONITOR_STEPS[currentStep]
  const isWelcomeStep = step.id === 'welcome'

  return (
    <>
      {/* Overlay backdrop */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.7)',
          zIndex: 9998,
          backdropFilter: 'blur(2px)',
          animation: 'fadeIn 0.3s ease'
        }}
        onClick={isWelcomeStep ? undefined : handleSkip}
      />

      {/* Highlight spotlight */}
      {highlightedElement && (
        <div
          style={{
            position: 'fixed',
            top: highlightedElement.getBoundingClientRect().top - 8,
            left: highlightedElement.getBoundingClientRect().left - 8,
            width: highlightedElement.getBoundingClientRect().width + 16,
            height: highlightedElement.getBoundingClientRect().height + 16,
            border: '3px solid var(--accent-amber)',
            borderRadius: 'var(--radius-md)',
            zIndex: 9999,
            boxShadow: '0 0 0 4px rgba(232, 188, 93, 0.3), 0 0 40px rgba(232, 188, 93, 0.5)',
            pointerEvents: 'none',
            animation: 'pulse 2s infinite'
          }}
        />
      )}

      {/* Tour card */}
      <OnboardingCard
        step={step}
        currentStep={currentStep}
        totalSteps={MONITOR_STEPS.length}
        onNext={handleNext}
        onBack={handleBack}
        onSkip={handleSkip}
        isWelcome={isWelcomeStep}
      />

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.02); opacity: 0.8; }
        }
      `}</style>
    </>
  )
}

function OnboardingCard({ step, currentStep, totalSteps, onNext, onBack, onSkip, isWelcome }) {
  const getPosition = () => {
    if (isWelcome || step.position === 'center' || !step.highlight) {
      return {
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)'
      }
    }

    // Position based on highlighted element
    const highlighted = document.querySelector(step.highlight)
    if (!highlighted) {
      return { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }
    }

    const rect = highlighted.getBoundingClientRect()
    const position = {}

    if (step.position === 'bottom-right') {
      position.top = rect.bottom + 20
      position.right = window.innerWidth - rect.right
    } else if (step.position === 'top-left') {
      position.bottom = window.innerHeight - rect.top + 20
      position.left = rect.left
    }

    return position
  }

  return (
    <div
      style={{
        position: 'fixed',
        ...getPosition(),
        width: isWelcome ? 500 : 420,
        maxWidth: '90vw',
        background: 'var(--bg-surface)',
        border: '2px solid var(--accent-amber)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.4)',
        zIndex: 10000,
        animation: 'slideIn 0.4s ease'
      }}
    >
      {/* Header */}
      <div style={{
        padding: '20px 24px',
        borderBottom: '1px solid var(--border)',
        background: 'linear-gradient(135deg, rgba(232, 188, 93, 0.1) 0%, rgba(232, 188, 93, 0.05) 100%)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <h3 style={{
            fontFamily: 'var(--font-sans)',
            fontSize: 18,
            fontWeight: 600,
            color: 'var(--text-primary)',
            margin: 0
          }}>
            {step.title}
          </h3>
          {!isWelcome && (
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: 'var(--accent-amber)',
              background: 'rgba(232, 188, 93, 0.15)',
              padding: '4px 10px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--accent-amber-dim)'
            }}>
              {currentStep}/{totalSteps - 1}
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: '24px' }}>
        <p style={{
          fontFamily: 'var(--font-sans)',
          fontSize: 14,
          lineHeight: 1.6,
          color: 'var(--text-secondary)',
          margin: '0 0 16px 0'
        }}>
          {step.message}
        </p>

        {step.tip && (
          <div style={{
            padding: '12px 14px',
            background: 'rgba(59, 130, 246, 0.08)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            borderRadius: 'var(--radius-md)',
            marginBottom: 16
          }}>
            <p style={{
              fontFamily: 'var(--font-sans)',
              fontSize: 13,
              lineHeight: 1.5,
              color: 'var(--text-primary)',
              margin: 0
            }}>
              {step.tip}
            </p>
          </div>
        )}

        {/* Action buttons */}
        <div style={{
          display: 'flex',
          gap: 10,
          justifyContent: isWelcome ? 'flex-end' : 'space-between'
        }}>
          {!isWelcome && currentStep > 0 && (
            <button
              onClick={onBack}
              style={{
                padding: '10px 18px',
                background: 'transparent',
                border: '1px solid var(--border-active)',
                borderRadius: 'var(--radius-sm)',
                fontFamily: 'var(--font-sans)',
                fontSize: 13,
                fontWeight: 500,
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'var(--bg-surface-2)'
                e.target.style.color = 'var(--text-primary)'
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent'
                e.target.style.color = 'var(--text-secondary)'
              }}
            >
              ← Back
            </button>
          )}

          <div style={{ display: 'flex', gap: 10, marginLeft: 'auto' }}>
            <button
              onClick={onSkip}
              style={{
                padding: '10px 18px',
                background: 'transparent',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                fontFamily: 'var(--font-sans)',
                fontSize: 13,
                fontWeight: 500,
                color: 'var(--text-muted)',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.target.style.borderColor = 'var(--border-active)'
                e.target.style.color = 'var(--text-secondary)'
              }}
              onMouseLeave={(e) => {
                e.target.style.borderColor = 'var(--border)'
                e.target.style.color = 'var(--text-muted)'
              }}
            >
              {isWelcome ? 'Skip Tour' : 'Skip'}
            </button>

            <button
              onClick={onNext}
              style={{
                padding: '10px 20px',
                background: 'var(--accent-amber)',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                fontFamily: 'var(--font-sans)',
                fontSize: 13,
                fontWeight: 600,
                color: 'var(--bg-base)',
                cursor: 'pointer',
                transition: 'all 0.2s',
                boxShadow: '0 2px 8px rgba(232, 188, 93, 0.3)'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#d4a843'
                e.target.style.transform = 'translateY(-1px)'
                e.target.style.boxShadow = '0 4px 12px rgba(232, 188, 93, 0.4)'
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'var(--accent-amber)'
                e.target.style.transform = 'translateY(0)'
                e.target.style.boxShadow = '0 2px 8px rgba(232, 188, 93, 0.3)'
              }}
            >
              {currentStep === totalSteps - 1 ? 'Finish Tour ✓' : isWelcome ? 'Start Tour →' : 'Next →'}
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translate(-50%, -40%);
          }
          to {
            opacity: 1;
            transform: translate(-50%, -50%);
          }
        }
      `}</style>
    </div>
  )
}
