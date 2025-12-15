import React from "react";
import { Link } from "react-router-dom";
import styles from "./Dashboard.module.css";

const Dashboard = () => {
  return (
    <div className={styles.dashboard}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.logo}>
          <div className={styles.logoIcon}>O</div>
          <span className={styles.logoText}>ONTIME</span>
        </div>
        <div className={styles.searchBar}>
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          <input type="text" placeholder="Search modules, reports..." />
        </div>
        <div className={styles.headerActions}>
          <div className={styles.notificationIcon}>
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
            <span className={styles.notificationDot}></span>
          </div>
          <div className={styles.settingsIcon}>
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M12 1v6m0 6v6m9-9h-6m-6 0H3m15.364 6.364L16.95 16.95m-9.9-9.9L4.636 4.636m14.728 0L16.95 7.05m-9.9 9.9L4.636 19.364"></path>
            </svg>
          </div>
          <div className={styles.userProfile}>
            <div className={styles.avatar}>JD</div>
            <span className={styles.userName}>John Doe</span>
          </div>
        </div>
      </header>

      <div className={styles.content}>
        {/* Main Content Area */}
        <div className={styles.mainContent}>
          {/* Welcome Section */}
          <div className={styles.welcomeSection}>
            <h1 className={styles.welcomeTitle}>Welcome back, John</h1>
            <p className={styles.welcomeSubtitle}>
              Here's what's happening with your business today.
            </p>
          </div>

          {/* KPI Cards */}
          <div className={styles.kpiGrid}>
            <div className={styles.kpiCard}>
              <div
                className={styles.kpiIcon}
                style={{ backgroundColor: "#FFE5B4" }}
              >
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <line x1="12" y1="1" x2="12" y2="23"></line>
                  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                </svg>
              </div>
              <div className={styles.kpiContent}>
                <h3 className={styles.kpiTitle}>Total Revenue</h3>
                <p className={styles.kpiValue}>$124,592</p>
                <div className={styles.kpiTrend}>
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                    <polyline points="17 6 23 6 23 12"></polyline>
                  </svg>
                  <span style={{ color: "#10B981" }}>+12.5%</span>
                </div>
              </div>
            </div>

            <div className={styles.kpiCard}>
              <div
                className={styles.kpiIcon}
                style={{ backgroundColor: "#E0E7FF" }}
              >
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="9" cy="21" r="1"></circle>
                  <circle cx="20" cy="21" r="1"></circle>
                  <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
                </svg>
              </div>
              <div className={styles.kpiContent}>
                <h3 className={styles.kpiTitle}>Orders Today</h3>
                <p className={styles.kpiValue}>48</p>
                <div className={styles.kpiTrend}>
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                    <polyline points="17 6 23 6 23 12"></polyline>
                  </svg>
                  <span style={{ color: "#10B981" }}>+8.2%</span>
                </div>
              </div>
            </div>

            <div className={styles.kpiCard}>
              <div
                className={styles.kpiIcon}
                style={{ backgroundColor: "#D1FAE5" }}
              >
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="9" cy="7" r="4"></circle>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
              </div>
              <div className={styles.kpiContent}>
                <h3 className={styles.kpiTitle}>Active Customers</h3>
                <p className={styles.kpiValue}>1,429</p>
                <div className={styles.kpiTrend}>
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                    <polyline points="17 6 23 6 23 12"></polyline>
                  </svg>
                  <span style={{ color: "#10B981" }}>+3.1%</span>
                </div>
              </div>
            </div>

            <div className={styles.kpiCard}>
              <div
                className={styles.kpiIcon}
                style={{ backgroundColor: "#FCE7F3" }}
              >
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                </svg>
              </div>
              <div className={styles.kpiContent}>
                <h3 className={styles.kpiTitle}>Growth Rate</h3>
                <p className={styles.kpiValue}>23.5%</p>
                <div className={styles.kpiTrend}>
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline>
                    <polyline points="17 18 23 18 23 12"></polyline>
                  </svg>
                  <span style={{ color: "#EF4444" }}>-2.4%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Modules Section */}
          <div className={styles.modulesSection}>
            <h2 className={styles.sectionTitle}>Modules</h2>
            <div className={styles.modulesGrid}>
              <Link to="/attendance" className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#10B981" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="8.5" cy="7" r="4"></circle>
                    <path d="M20 8v6"></path>
                    <path d="M23 11h-6"></path>
                  </svg>
                </div>
                <span className={styles.moduleName}>Attendance</span>
              </Link>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#F97316" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <circle cx="9" cy="21" r="1"></circle>
                    <circle cx="20" cy="21" r="1"></circle>
                    <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
                  </svg>
                </div>
                <span className={styles.moduleName}>Sales</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#3B82F6" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <rect
                      x="3"
                      y="3"
                      width="18"
                      height="18"
                      rx="2"
                      ry="2"
                    ></rect>
                    <line x1="9" y1="3" x2="9" y2="21"></line>
                    <line x1="3" y1="9" x2="21" y2="9"></line>
                  </svg>
                </div>
                <span className={styles.moduleName}>Inventory</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#84CC16" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                  </svg>
                </div>
                <span className={styles.moduleName}>Customers</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#A855F7" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                  </svg>
                </div>
                <span className={styles.moduleName}>Invoicing</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#EF4444" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <line x1="18" y1="20" x2="18" y2="10"></line>
                    <line x1="12" y1="20" x2="12" y2="4"></line>
                    <line x1="6" y1="20" x2="6" y2="14"></line>
                  </svg>
                </div>
                <span className={styles.moduleName}>Reports</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#10B981" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                    <polyline points="9 22 9 12 15 12 15 22"></polyline>
                  </svg>
                </div>
                <span className={styles.moduleName}>Warehouse</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#EAB308" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M1 3h15v13H1z"></path>
                    <path d="M16 8h4l3 3v5h-7V8z"></path>
                    <circle cx="5.5" cy="18.5" r="2.5"></circle>
                    <circle cx="18.5" cy="18.5" r="2.5"></circle>
                  </svg>
                </div>
                <span className={styles.moduleName}>Shipping</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#EF4444" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <rect
                      x="1"
                      y="4"
                      width="22"
                      height="16"
                      rx="2"
                      ry="2"
                    ></rect>
                    <line x1="1" y1="10" x2="23" y2="10"></line>
                  </svg>
                </div>
                <span className={styles.moduleName}>Payments</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#F97316" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <rect
                      x="3"
                      y="4"
                      width="18"
                      height="18"
                      rx="2"
                      ry="2"
                    ></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                  </svg>
                </div>
                <span className={styles.moduleName}>Calendar</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#6B7280" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                </div>
                <span className={styles.moduleName}>Messages</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#84CC16" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="8.5" cy="7" r="4"></circle>
                    <path d="M20 8v6"></path>
                    <path d="M23 11h-6"></path>
                  </svg>
                </div>
                <span className={styles.moduleName}>HR</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#A855F7" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="9 11 12 14 22 4"></polyline>
                    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
                  </svg>
                </div>
                <span className={styles.moduleName}>Tasks</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#EC4899" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M12 1v6m0 6v6m9-9h-6m-6 0H3m15.364 6.364L16.95 16.95m-9.9-9.9L4.636 4.636m14.728 0L16.95 7.05m-9.9 9.9L4.636 19.364"></path>
                  </svg>
                </div>
                <span className={styles.moduleName}>Settings</span>
              </div>

              <div className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#10B981" }}>
                  <svg
                    width="32"
                    height="32"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                  </svg>
                </div>
                <span className={styles.moduleName}>Support</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className={styles.sidebar}>
          {/* Quick Actions */}
          <div className={styles.quickActionsSection}>
            <h2 className={styles.sectionTitle}>Quick Actions</h2>
            <div className={styles.quickActionsGrid}>
              <button
                className={styles.quickActionBtn}
                style={{ backgroundColor: "#F97316", color: "white" }}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="9" cy="21" r="1"></circle>
                  <circle cx="20" cy="21" r="1"></circle>
                  <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
                </svg>
                <span>New Sale</span>
              </button>

              <button
                className={styles.quickActionBtn}
                style={{ backgroundColor: "#1E40AF", color: "white" }}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="9" y1="3" x2="9" y2="21"></line>
                  <line x1="3" y1="9" x2="21" y2="9"></line>
                </svg>
                <span>Add Product</span>
              </button>

              <button
                className={styles.quickActionBtn}
                style={{ backgroundColor: "#0891B2", color: "white" }}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                </svg>
                <span>New Invoice</span>
              </button>

              <button
                className={styles.quickActionBtn}
                style={{ backgroundColor: "#10B981", color: "white" }}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="9" cy="7" r="4"></circle>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                <span>Add Customer</span>
              </button>
            </div>
          </div>

          {/* Recent Activity */}
          <div className={styles.recentActivitySection}>
            <h2 className={styles.sectionTitle}>
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                style={{ display: "inline", marginRight: "8px" }}
              >
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
              Recent Activity
            </h2>
            <div className={styles.activityList}>
              <div className={styles.activityItem}>
                <div
                  className={styles.activityIcon}
                  style={{ backgroundColor: "#F97316" }}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <circle cx="9" cy="21" r="1"></circle>
                    <circle cx="20" cy="21" r="1"></circle>
                    <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
                  </svg>
                </div>
                <div className={styles.activityContent}>
                  <p className={styles.activityTitle}>New order #1234</p>
                  <p className={styles.activityDescription}>
                    John Smith placed an order
                  </p>
                  <span className={styles.activityTime}>2 min ago</span>
                </div>
              </div>

              <div className={styles.activityItem}>
                <div
                  className={styles.activityIcon}
                  style={{ backgroundColor: "#3B82F6" }}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <rect
                      x="3"
                      y="3"
                      width="18"
                      height="18"
                      rx="2"
                      ry="2"
                    ></rect>
                    <line x1="9" y1="3" x2="9" y2="21"></line>
                    <line x1="3" y1="9" x2="21" y2="9"></line>
                  </svg>
                </div>
                <div className={styles.activityContent}>
                  <p className={styles.activityTitle}>Inventory updated</p>
                  <p className={styles.activityDescription}>
                    Stock adjusted for SKU-789
                  </p>
                  <span className={styles.activityTime}>15 min ago</span>
                </div>
              </div>

              <div className={styles.activityItem}>
                <div
                  className={styles.activityIcon}
                  style={{ backgroundColor: "#A855F7" }}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                  </svg>
                </div>
                <div className={styles.activityContent}>
                  <p className={styles.activityTitle}>Invoice sent</p>
                  <p className={styles.activityDescription}>
                    INV-456 sent to ABC Corp
                  </p>
                  <span className={styles.activityTime}>1 hour ago</span>
                </div>
              </div>

              <div className={styles.activityItem}>
                <div
                  className={styles.activityIcon}
                  style={{ backgroundColor: "#10B981" }}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                  </svg>
                </div>
                <div className={styles.activityContent}>
                  <p className={styles.activityTitle}>New customer</p>
                  <p className={styles.activityDescription}>
                    Emma Wilson registered
                  </p>
                  <span className={styles.activityTime}>2 hours ago</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
