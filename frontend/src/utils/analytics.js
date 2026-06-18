/**
 * Google Analytics tracking utility
 * 
 * Usage:
 *   trackEvent('demo_anomaly_clicked', { panel: 'monitor' })
 *   trackEvent('chat_message_sent', { has_tag: true })
 *   trackEvent('pdf_uploaded', { equipment: 'motor' })
 */

export const trackEvent = (eventName, eventParams = {}) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', eventName, eventParams)
    console.log('[Analytics] Event tracked:', eventName, eventParams)
  }
}

export const trackPageView = (pageName) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'page_view', {
      page_title: pageName,
      page_location: window.location.href,
    })
    console.log('[Analytics] Page view:', pageName)
  }
}

export const trackUserRole = (role) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'role_selected', {
      role: role,
    })
    console.log('[Analytics] User role:', role)
  }
}

export const trackAnalysisRun = (equipmentTag, severity) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'analysis_run', {
      equipment: equipmentTag,
      severity: severity,
    })
    console.log('[Analytics] Analysis run:', equipmentTag, severity)
  }
}

export const trackDocumentUpload = (equipmentTag, fileName) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'document_upload', {
      equipment: equipmentTag,
      file_name: fileName,
    })
    console.log('[Analytics] Document uploaded:', equipmentTag, fileName)
  }
}

export const trackChatMessage = (hasEquipmentTag, hasCitations) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'chat_message', {
      has_equipment_tag: hasEquipmentTag,
      has_citations: hasCitations,
    })
    console.log('[Analytics] Chat message sent')
  }
}
