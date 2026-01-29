# Mission State Matrix (Outcome/Qualifier Variant)

```cpp

// Flags / qualifiers
bool scheduled_pause = false;       // planned pause while executing
bool is_abnormal_completion = false; // true when completion is non-normal (abort/cancel/error)

// Qualifiers
enum class ExecutionMode {
    NORMAL,
    SCHEDULED_PAUSE
};

enum class CompletionOutcome {
    NONE,       // not terminal
    NORMAL,     // completed nominally
    ABORTED,    // operator or FC abort
    CANCELED,   // operator cancel
    ERROR       // failure/exception
};

// States

enum class MissionManagerState {
    NO_MISSION,
    MISSION_LOADED,
    // future states... 
};

enum class MissionState {
    QUEUED,
    EXECUTING,
    PAUSED,
    COMPLETED,
};

enum class StepState {
    LOADED,
    EXECUTING,
    PAUSED,
    COMPLETED,
};

enum class FlightStateSdk {
    DISARMED,
    LANDED_IDLE,
    LANDED_ARMED,
    TAKING_OFF,
    FLYING_MOVING,
    HOVER,
    LANDING,
    SAFETY,  //RTL
};

// Step types
enum class StepType {
    TAKEOFF,
    GOTO,
    WAIT,
    LAND,
    RTL,
};

// Actions (split by scope if needed)
enum class ManagerAction {
    LOAD_MISSION,
    START_MISSION,
    REMOVE_MISSION,
    STOP,
    LIP,
    RTL,
    GOTO_XYZ
};

enum class MissionAction {
    PAUSE,
    RESUME,     
    GOTO_WP,
};

enum class FCAction {
    CHANGE_MAX_SPEED,
    CHANGE_HOME
};

// Event names (string constants)
constexpr const char* EVT_LOADING_STARTED = "loading_started";
constexpr const char* EVT_LOADING_SUCCESS = "loading_success";
constexpr const char* EVT_LOADING_FAILED  = "loading_failed";

constexpr const char* EVT_MISSION_STARTED = "mission_started";
constexpr const char* EVT_MISSION_COMPLETED_NORMAL = "mission_completed_normal";
constexpr const char* EVT_MISSION_COMPLETED_ABORTED = "mission_completed_aborted";
constexpr const char* EVT_MISSION_COMPLETED_CANCELED = "mission_completed_canceled";
constexpr const char* EVT_MISSION_COMPLETED_ERROR = "mission_completed_error";
constexpr const char* EVT_MISSION_SCHEDULED_FOR_PAUSE = "mission_scheduled_for_pause";
constexpr const char* EVT_MISSION_PAUSED = "mission_paused";
constexpr const char* EVT_MISSION_RESUMED = "mission_resumed";

constexpr const char* EVT_STEP_LOADING_STARTED = "step_loading_started";
constexpr const char* EVT_STEP_LOADED = "step_loaded";
constexpr const char* EVT_STEP_LOADING_FAILED = "step_loading_failed";
constexpr const char* EVT_STEP_EXECUTING = "step_executing";
constexpr const char* EVT_STEP_SCHEDULED_FOR_PAUSE = "step_scheduled_for_pause";
constexpr const char* EVT_STEP_PAUSED = "step_paused";
constexpr const char* EVT_STEP_RESUMED = "step_resumed";
constexpr const char* EVT_STEP_COMPLETED = "step_completed";
constexpr const char* EVT_STEP_ABORTED = "step_aborted";
constexpr const char* EVT_STEP_CANCELED = "step_canceled";
```
