export type UserRole = "super_admin" | "admin";

export interface AuthUser {
  id: string;
  username: string;
  role: UserRole;
  createdAt: number;
  language: string;
}

export interface AuthStatus {
  needsSetup: boolean;
}

export interface UniversityStep {
  id: string;
  title: string;
  description: string;
  route: string;
  completed: boolean;
  locked: boolean;
}

export interface UniversityCourse {
  id: string;
  title: string;
  shortTitle: string;
  description: string | null;
  available: boolean;
  active: boolean;
  graduatedAt: number | null;
  requires?: string | null;
  steps: UniversityStep[];
}

export interface AdminBasicsStatus {
  userId: string;
  username: string;
  graduatedAt: number | null;
}

export interface UniversityCatalog {
  activeCourse: string | null;
  courses: UniversityCourse[];
}

export interface InviteCode {
  code: string;
  createdAt: number;
  usedBy: string | null;
}

export type SettingFieldType = "bool" | "int" | "float" | "string" | "enum" | "raw";

export interface SettingField {
  key: string;
  type: SettingFieldType;
  value: boolean | number | string;
  label: string;
  description: string | null;
  help: string | null;
  group: string;
  options: { value: string; label: string; description: string | null }[] | null;
  sensitive: boolean;
  popular: boolean;
}

export type ServerRunState = "online" | "offline" | "starting" | "stopping" | "restarting";

export interface ServerStatus {
  state: ServerRunState;
  map: string;
  uptimeSeconds: number;
  cpuPercent: number;
  ramUsedGB: number;
  ramTotalGB: number;
  systemCpuPercent: number;
  systemRamUsedGB: number;
  tickRateMs: number | null;
  targetTickRateMs: number;
  playersOnline: number;
  maxPlayers: number;
  serverVersion: string;
  modCount: number;
  lastSavedAt: string;
}

export interface ServerUpdateCheck {
  installedBuildId: string | null;
  latestBuildId: string | null;
  updateAvailable: boolean;
  canCompare: boolean;
}

export interface WorkshopUpdateAllResult {
  updated: number;
  updatedWorkshopIds?: string[];
  backup: { timestamp: string; folder: string; folders?: string[] } | null;
  mods: Mod[];
}


export interface WorkshopCacheItem {
  workshopId: string;
  name: string;
  author: string;
  description: string;
  previewUrl?: string | null;
  packageName?: string | null;
  status: "ready" | "installed" | "update_available" | "invalid";
  valid: boolean;
  validationError?: string | null;
  sourcePath: string;
  sizeBytes: number;
  downloadedAt: number;
  installedUpdatedAt: number;
}

export interface WorkshopUpdateCheck {
  checked: number;
  updatesAvailable: number;
  upToDate: boolean;
  mods: Mod[];
}

export type ServerUpdateJobStatus = "running" | "done" | "error";

export interface ServerUpdateJob {
  status: ServerUpdateJobStatus;
  log: string[];
  error: string | null;
  installedBuildId: string | null;
  latestBuildId: string | null;
}

export type ConnectionStatus = "online" | "idle" | "offline";

export interface Player {
  id: string;
  characterName: string;
  steamId: string;
  level: number;
  guild: string | null;
  pingMs: number;
  onlineSeconds: number;
  connectionStatus: ConnectionStatus;
  joinedAt: string;
  isBanned: boolean;
  avatarSeed: string;
}

export type ModStatus = "enabled" | "disabled" | "broken";

export interface Mod {
  id: string;
  name: string;
  version: string;
  author: string;
  description: string;
  dependencies: string[];
  status: ModStatus;
  loadPriority: number;
  updateAvailable: boolean;
  latestVersion?: string;
  sourceModId?: number | null;
  workshopId?: string | null;
  packageName?: string | null;
  previewUrl?: string | null;
  source?: "steam_workshop" | "manual" | string;
  manuallyInstalled?: boolean;
  deploymentStatus?: "configured" | "pending" | "deployed" | "restart_failed" | "disabled";
  deploymentMessage?: string;
}

export interface VerifiedFileInstall {
  token: string;
  verified: boolean;
  modName: string;
  author: string;
  version: string;
  sizeBytes: number;
}

export type LogLevel = "info" | "warning" | "error" | "debug";

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  source: string;
  message: string;
  instanceId?: string | null;
}

export interface LogStreams {
  app: LogEntry[];
  activity: LogEntry[];
}

export interface ServerSettings {
  serverName: string;
  serverPassword: string;
  maxPlayers: number;
  difficulty: "easy" | "normal" | "hard";
  pvpEnabled: boolean;
  expRate: number;
  dayNightLengthMinutes: number;
}

export interface SystemSettings {
  bootWithWindows: boolean;
  autoStartActiveServer: boolean;
  privacyMode: boolean;
  adminPort: number;
  debugLogging: boolean;
}

export interface ScheduleConfig {
  enabled: boolean;
  frequency: "daily" | "weekly";
  dayOfWeek: number; // 0=Monday..6=Sunday, used only when frequency === "weekly"
  hour: number; // 0-23
}

export interface RestartScheduleConfig extends ScheduleConfig {
  warningMinutes: number;
}

export interface BackupRetentionConfig {
  maxCount: number | null;
  maxAgeDays: number | null;
  maxTotalBytes: number | null;
}

export interface AutomationConfig {
  backup: ScheduleConfig;
  restart: RestartScheduleConfig;
  joinLeaveMessages: boolean;
  backupRetention: BackupRetentionConfig;
  rconReady: boolean;
}

export type BackupKind = "manual" | "scheduled" | "pre_import" | "pre_restore" | "pre_mod_update";

export interface BackupRecord {
  timestamp: string;
  kind: BackupKind;
  sizeBytes: number;
  fileCount: number | null;
  liveSaveForced: boolean;
  notes: string;
  hasManifest: boolean;
  folder: string;
}

export type BackupVerifyStatus = "ok" | "corrupted" | "unknown";

export interface BackupVerifyResult {
  status: BackupVerifyStatus;
  issues: string[];
}

export interface BackupRestoreResult {
  restoredFrom: string;
  serverWasStopped: boolean;
  rollbackSnapshot: string | null;
}

export interface SaveImportCandidate {
  path: string;
  name: string;
  sizeBytes: number;
  modified: string;
  valid: boolean;
  issues: string[];
}

export interface SaveImportResult {
  importedFrom: string;
  worldName: string;
  backupCreated: boolean;
}

export type NotificationKind = "success" | "info" | "warning" | "error";

export interface AppNotification {
  id: string;
  kind: NotificationKind;
  title: string;
  message?: string;
  createdAt: number;
}

export interface AppUpdateStatus {
  currentVersion: string;
  latestVersion: string | null;
  updateAvailable: boolean;
  releaseUrl: string | null;
  releaseName: string | null;
  publishedAt: string | null;
  available: boolean;
  configured?: boolean;
  message?: string | null;
  installerAvailable?: boolean;
  installSupported?: boolean;
  installing?: boolean;
  installPhase?: string;
  installProgress?: number;
  installMessage?: string | null;
  installError?: string | null;
  targetVersion?: string | null;
  channel?: string;
  repository?: string;
}

export interface NexusAccount {
  connected: boolean;
  username?: string;
  userId?: number;
  isPremium?: boolean;
  membershipRoles?: string[];
  premiumExpiry?: number | string | null;
  lastAccountSyncAt?: number | null;
  avatarInitial?: string;
}

export interface NexusOAuthStart {
  requestId: string;
  authorizeUrl: string;
}

export type NexusOAuthStatus =
  { status: "pending" } | { status: "connected"; account: NexusAccount } | { status: "error"; message: string };

export type SteamWorkshopList = "trending" | "latest_added" | "latest_updated";

export interface SteamWorkshopResult {
  id: string;
  workshopId: string;
  name: string;
  author: string;
  summary: string;
  categoryName: string;
  subscriptions: number;
  favorites: number;
  pictureUrl?: string;
  timeCreated: number;
  timeUpdated: number;
  fileSize: number;
  steamUrl: string;
}

export interface SteamWorkshopPage {
  results: SteamWorkshopResult[];
  totalCount: number;
}

export type NexusModList = "trending" | "latest_added" | "latest_updated";

export interface NexusModResult {
  id: string;
  modId: number;
  name: string;
  author: string;
  summary: string;
  version: string;
  categoryId: number | null;
  categoryName: string;
  downloads: number;
  endorsements: number;
  pictureUrl?: string;
  directDownloadEnabled: boolean;
  nexusUrl?: string;
  steamUrl?: string;
}

export interface NexusModPage {
  results: NexusModResult[];
  totalCount: number;
}

export interface DownloadedNexusMod {
  id: string;
  modId: number;
  fileId?: number | null;
  name: string;
  author: string;
  version: string;
  description: string;
  previewUrl?: string | null;
  nexusUrl?: string | null;
  status: "installed" | "configured" | "downloaded" | "missing";
  enabled: boolean;
  installKind: string;
  installMode: string;
  packageName?: string | null;
  sourcePath?: string | null;
  deployedPath?: string | null;
  configured: boolean;
  deploymentStatus: string;
  deploymentMessage?: string | null;
  recoveredFromDisk?: boolean;
  folderName?: string | null;
  installedPath?: string | null;
  installedPaths?: string[];
  downloadedFile?: string | null;
  archiveAvailable: boolean;
  sizeBytes: number;
  loadPriority: number;
  installedAt?: string | null;
  runtimeVerification?: {
    state: "verified" | "warning" | "failed";
    evidence: string;
    confidence: "high" | "medium" | "low";
    checkedAt: string;
    paths: string[];
  } | null;
}

export interface NexusModFile {
  fileId: number;
  name: string;
  version: string;
  category: string;
  isMain: boolean;
  sizeKb?: number | null;
  description: string;
}

export interface ModWishlistRequest {
  id: string;
  source?: "nexus" | "steam";
  nexusModId?: number;
  workshopId?: string;
  name: string;
  author: string;
  summary: string;
  pictureUrl?: string;
  nexusUrl?: string;
  steamUrl?: string;
  requestedBy: string;
  requestedAt: string;
}

export type ModsPathSource = "override" | "derived" | null;
export type InstanceSource = "steam" | "manual" | "deployed";

export interface ServerInstance {
  id: string;
  name: string;
  serverPath: string;
  source: InstanceSource;
  gamePort: number;
  effectiveGamePort: number;
  queryPort: number;
  rconPort: number;
  communityServer: boolean;
  usePerfThreads: boolean;
  noAsyncLoadingThread: boolean;
  useMultithreadForDs: boolean;
  usePublicIpOverride: boolean;
  publicIpOverride: string;
  usePublicPortOverride: boolean;
  useQueryPort: boolean;
  performanceFlags: boolean;
  workerThreads: number | null;
  jsonLogFormat: boolean;
  archived?: boolean;
  createdAt: number;
  exists: boolean;
  executableFound: boolean;
  modsPath: string | null;
  modsPathSource: ModsPathSource;
  modsPathExists: boolean;
  ue4ssInstalled: boolean;
  ue4ssVersion: string | null;
}

export interface InstanceListView {
  activeId: string | null;
  instances: ServerInstance[];
}

export type DeployJobStatus = "running" | "done" | "error";

export interface DeployJob {
  status: DeployJobStatus;
  log: string[];
  error: string | null;
  instanceId: string | null;
}

export interface ModsPathInfo {
  modsPath: string | null;
  source: ModsPathSource;
  exists: boolean;
}

export interface Ue4ssStatus {
  installed: boolean;
  installedVersion: string | null;
}

export interface Ue4ssLatest {
  version: string;
  assetName: string;
  downloadUrl: string;
  size: number;
}

export interface PortMappingInfo {
  internalClient: string;
  isThisMachine: boolean;
  description: string;
}

export interface UpnpStatus {
  available: boolean;
  routerName: string | null;
  externalIp: string | null;
  localIp: string | null;
  port: number | null;
  queryPort: number | null;
  adminPort: number;
  gameMapping: PortMappingInfo | null;
  queryMapping: PortMappingInfo | null;
  adminMapping: PortMappingInfo | null;
  gameVerified: boolean;
  queryVerified: boolean;
  adminVerified: boolean;
}

export interface PortForwardResult {
  port: number;
  externalIp: string | null;
  routerName: string;
}


export interface WorkshopDetails {
  workshopId: string;
  title: string;
  description: string;
  previewUrl: string | null;
  fileSize: number;
  timeCreated: number;
  timeUpdated: number;
  owner: string;
  subscriptions: number;
}

export interface InstanceOverviewItem {
  id: string;
  name: string;
  state: ServerRunState;
  map: string;
  uptimeSeconds: number;
  lastSavedAt: string;
  playersOnline: number;
  maxPlayers: number;
  gamePort: number;
  archived: boolean;
}

export interface InstanceOverview {
  activeId: string | null;
  instances: InstanceOverviewItem[];
}

export interface FirewallRuleStatus {
  name: string;
  port: number;
  protocol: "TCP" | "UDP";
  exists: boolean;
}

export interface InstanceFirewallStatus {
  instanceId: string;
  instanceName: string;
  healthy: boolean;
  rules: FirewallRuleStatus[];
}

export interface BackupServerGroup {
  instanceId: string;
  instanceName: string;
  totalBytes: number;
  backups: BackupRecord[];
}

export interface BackupCenterResponse {
  servers: BackupServerGroup[];
}

export interface PerformanceSnapshot {
  instanceId: string;
  instanceName: string;
  serverPath: string;
  state: ServerRunState;
  uptimeSeconds: number;
  serverCpuPercent: number;
  serverRamBytes: number;
  systemCpuPercent: number;
  systemRamUsedBytes: number;
  systemRamTotalBytes: number;
  systemRamPercent: number;
  logicalCpuCount: number;
  physicalCpuCount: number;
  diskUsedBytes: number;
  diskTotalBytes: number;
  diskPercent: number;
  diskReadBytesPerSecond: number;
  diskWriteBytesPerSecond: number;
  networkUploadBytesPerSecond: number;
  networkDownloadBytesPerSecond: number;
  sampledAt: number;
}

export interface InstancePerformanceRow {
  instanceId: string;
  instanceName: string;
  state: ServerRunState;
  uptimeSeconds: number;
  serverCpuPercent: number;
  serverRamBytes: number;
  gamePort: number;
}

export interface InstancePerformanceResponse {
  instances: InstancePerformanceRow[];
}

export type QueueTaskStatus = "queued" | "running" | "paused" | "cancelling" | "completed" | "failed" | "cancelled";
export type QueueTaskLogLevel = "info" | "warning" | "error" | "debug";

export interface QueueTaskLogEntry {
  timestamp: number;
  level: QueueTaskLogLevel;
  message: string;
}

export interface QueueTask {
  id: string;
  action: string;
  title: string;
  instanceId: string | null;
  payload: Record<string, unknown>;
  status: QueueTaskStatus;
  priority: number;
  progress: number;
  message: string;
  log: QueueTaskLogEntry[];
  result: unknown;
  error: string | null;
  createdBy: string | null;
  createdAt: number;
  startedAt: number | null;
  finishedAt: number | null;
  updatedAt: number;
  attempt: number;
  maxRetries: number;
  cancelRequested: boolean;
  pauseRequested: boolean;
  etaSeconds: number | null;
}

export interface TaskQueueResponse {
  tasks: QueueTask[];
}


export interface PersistentNotification {
  id: string; kind: NotificationKind; titleKey: string; messageKey: string | null; params: Record<string, string | number>; fallbackTitle: string; fallbackMessage: string; instanceId: string | null; category: string; actionUrl: string | null; createdAt: number; read: boolean;
}
export interface NotificationCenterResponse { notifications: PersistentNotification[]; unreadCount: number; }
export interface ActivityEvent { id:string; timestamp:string|number; level:"info"|"warning"|"error"|"debug"; source:string; sourceKey?:string; message:string; technicalDetails?:string|null; instanceId?:string|null; category:"server"|"application"|"task"; categoryKey?:string; eventType:string; taskId?:string; status?:string; progress?:number; }
export interface ActivityCenterResponse { events: ActivityEvent[]; }
