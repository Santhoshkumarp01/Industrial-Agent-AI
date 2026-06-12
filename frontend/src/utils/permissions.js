/**
 * Role-based access control utilities
 */

export const ROLES = {
  ENGINEER: 'engineer',
  MANAGER: 'manager',
  TECHNICIAN: 'technician',
  JUDGE: 'judge',
}

export const PERMISSIONS = {
  // Chat features
  CHAT_SEND_MESSAGE: [ROLES.ENGINEER, ROLES.JUDGE],
  CHAT_VIEW_HISTORY: [ROLES.ENGINEER, ROLES.MANAGER, ROLES.TECHNICIAN, ROLES.JUDGE],
  
  // Document features
  UPLOAD_DOCUMENT: [ROLES.ENGINEER, ROLES.JUDGE],
  DELETE_DOCUMENT: [ROLES.ENGINEER, ROLES.JUDGE],
  VIEW_DOCUMENTS: [ROLES.ENGINEER, ROLES.MANAGER, ROLES.TECHNICIAN, ROLES.JUDGE],
  
  // Monitoring features
  VIEW_MONITORING: [ROLES.ENGINEER, ROLES.MANAGER, ROLES.TECHNICIAN, ROLES.JUDGE],
  TRIGGER_DEMO_ANOMALY: [ROLES.ENGINEER, ROLES.JUDGE],
  RUN_ANALYSIS: [ROLES.ENGINEER, ROLES.JUDGE],
  
  // Reports and logbook
  VIEW_REPORTS: [ROLES.ENGINEER, ROLES.MANAGER, ROLES.TECHNICIAN, ROLES.JUDGE],
  EDIT_REPORTS: [ROLES.ENGINEER, ROLES.JUDGE],
  VIEW_LOGBOOK: [ROLES.ENGINEER, ROLES.MANAGER, ROLES.TECHNICIAN, ROLES.JUDGE],
  EDIT_LOGBOOK: [ROLES.ENGINEER, ROLES.JUDGE],
  UPDATE_LOGBOOK_STATUS: [ROLES.ENGINEER, ROLES.TECHNICIAN, ROLES.JUDGE],
  
  // Feedback
  SUBMIT_FEEDBACK: [ROLES.ENGINEER, ROLES.JUDGE],
  VIEW_FEEDBACK_STATS: [ROLES.ENGINEER, ROLES.MANAGER, ROLES.JUDGE],
}

/**
 * Check if user role has permission for an action
 */
export function hasPermission(userRole, permission) {
  if (!userRole || !permission) return false
  const allowedRoles = PERMISSIONS[permission]
  return allowedRoles ? allowedRoles.includes(userRole) : false
}

/**
 * Get role display info
 */
export function getRoleInfo(roleId) {
  const roleMap = {
    engineer: {
      title: 'Maintenance Engineer',
      badge: 'ENGINEER',
      color: 'var(--accent-blue)',
    },
    manager: {
      title: 'Plant Manager',
      badge: 'MANAGER',
      color: 'var(--accent-amber)',
    },
    technician: {
      title: 'Field Technician',
      badge: 'TECHNICIAN',
      color: 'var(--status-ok)',
    },
    judge: {
      title: 'Judge / Demo',
      badge: 'DEMO MODE',
      color: '#B388FF',
    },
  }
  return roleMap[roleId] || null
}
