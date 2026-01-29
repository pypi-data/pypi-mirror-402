/**
 * MSW handlers for Maintenance API
 */

import { http, HttpResponse } from "msw";

const API_BASE = "/api/v1/maintenance";

// In-memory retention config
let retentionConfig = {
  validation_retention_days: 90,
  profile_keep_per_source: 5,
  notification_log_retention_days: 30,
  run_vacuum: true,
  enabled: true,
};

// Track last maintenance run
let lastMaintenanceRun: string | null = null;

// Available cleanup tasks
const AVAILABLE_TASKS = [
  "validation_cleanup",
  "profile_cleanup",
  "notification_log_cleanup",
];

export const maintenanceHandlers = [
  // GET /maintenance/retention - Get retention policy
  http.get(`${API_BASE}/retention`, () => {
    return HttpResponse.json(retentionConfig);
  }),

  // PUT /maintenance/retention - Update retention policy
  http.put(`${API_BASE}/retention`, async ({ request }) => {
    const body = (await request.json()) as typeof retentionConfig;

    // Update config
    retentionConfig = {
      ...retentionConfig,
      ...body,
    };

    return HttpResponse.json(retentionConfig);
  }),

  // GET /maintenance/status - Get maintenance status
  http.get(`${API_BASE}/status`, () => {
    // Calculate next scheduled run (next day at 3:00 AM)
    const now = new Date();
    const nextRun = new Date(now);
    nextRun.setDate(nextRun.getDate() + 1);
    nextRun.setHours(3, 0, 0, 0);

    return HttpResponse.json({
      enabled: retentionConfig.enabled,
      last_run_at: lastMaintenanceRun,
      next_scheduled_at: retentionConfig.enabled ? nextRun.toISOString() : null,
      config: retentionConfig,
      available_tasks: AVAILABLE_TASKS,
    });
  }),

  // POST /maintenance/cleanup - Trigger cleanup
  http.post(`${API_BASE}/cleanup`, async ({ request }) => {
    const body = (await request.json()) as {
      tasks?: string[];
      run_vacuum?: boolean;
    };

    const startedAt = new Date();

    // Simulate cleanup time
    await new Promise((resolve) => setTimeout(resolve, 500));

    const tasksToRun = body.tasks || AVAILABLE_TASKS;
    const results = tasksToRun.map((task) => ({
      task_name: task,
      records_deleted: Math.floor(Math.random() * 100),
      duration_ms: 50 + Math.floor(Math.random() * 200),
      success: true,
      error: null,
    }));

    const completedAt = new Date();
    lastMaintenanceRun = completedAt.toISOString();

    return HttpResponse.json({
      started_at: startedAt.toISOString(),
      completed_at: completedAt.toISOString(),
      results,
      total_deleted: results.reduce((sum, r) => sum + r.records_deleted, 0),
      total_duration_ms: completedAt.getTime() - startedAt.getTime(),
      vacuum_performed: body.run_vacuum || false,
      vacuum_error: null,
      success: true,
    });
  }),

  // POST /maintenance/vacuum - Run vacuum
  http.post(`${API_BASE}/vacuum`, async () => {
    const startedAt = new Date();

    // Simulate vacuum time
    await new Promise((resolve) => setTimeout(resolve, 300));

    const completedAt = new Date();

    return HttpResponse.json({
      started_at: startedAt.toISOString(),
      completed_at: completedAt.toISOString(),
      results: [],
      total_deleted: 0,
      total_duration_ms: completedAt.getTime() - startedAt.getTime(),
      vacuum_performed: true,
      vacuum_error: null,
      success: true,
    });
  }),

  // GET /maintenance/cache/stats - Get cache statistics
  http.get(`${API_BASE}/cache/stats`, () => {
    return HttpResponse.json({
      total_entries: 42,
      expired_entries: 5,
      valid_entries: 37,
      max_size: 1000,
      hit_rate: 0.85,
    });
  }),

  // POST /maintenance/cache/clear - Clear cache
  http.post(`${API_BASE}/cache/clear`, async ({ request }) => {
    const body = (await request.json()) as {
      pattern?: string;
      namespace?: string;
    };

    // Simulate cache clear
    await new Promise((resolve) => setTimeout(resolve, 100));

    return HttpResponse.json({
      total_entries: body.pattern ? 35 : 0,
      expired_entries: 0,
      valid_entries: body.pattern ? 35 : 0,
      max_size: 1000,
      hit_rate: null,
    });
  }),
];
