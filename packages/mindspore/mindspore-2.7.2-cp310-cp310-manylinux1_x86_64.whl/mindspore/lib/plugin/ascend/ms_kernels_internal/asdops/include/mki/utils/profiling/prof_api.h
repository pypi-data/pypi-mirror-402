/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef PROFILING_API_H
#define PROFILING_API_H
#include <cstdint>
#include <cstdlib>

#ifdef __cplusplus
extern "C" {
#endif

#if (defined(_WIN32) || defined(_WIN64) || defined(_MSC_VER))
#define MSVP_PROF_API __declspec(dllexport)
#else
#define MSVP_PROF_API __attribute__((visibility("default")))
#endif

using ProfCommandHandle = int32_t (*)(uint32_t type, void *data, uint32_t len);

const uint32_t MSPROF_REPORT_DATA_MAGIC_NUM = 0x5a5a;

const uint16_t MSPROF_REPORT_ACL_LEVEL = 20000;
const uint16_t MSPROF_REPORT_NODE_LEVEL = 10000;

const uint32_t MSPROF_REPORT_ACL_OTHERS_BASE_TYPE = 0x40000;

const uint32_t MSPROF_REPORT_EXECUTE_TYPE_ID = 0xB6666;
const uint32_t MSPROF_REPORT_SETUP_TYPE_ID = 0xB8888;

const uint32_t MSPROF_REPORT_NODE_BASIC_INFO_TYPE = 0;
const uint32_t MSPROF_REPORT_NODE_LAUNCH_TYPE = 5;

const uint32_t MSPROF_GE_TENSOR_DATA_SHAPE_LEN = 8;
const uint32_t ATB_MSPROF_TENSOR_DATA_SIZE = 5;
const uint32_t MSPROF_REPORT_NODE_TENSOR_INFO_TYPE = 1;
const uint32_t MSPROF_CTX_ID_MAX_NUM = 55;
const uint32_t MSPROF_REPORT_NODE_CONTEXT_ID_INFO_TYPE = 4;

const int32_t PROFILING_REPORT_SUCCESS = 0;
const int32_t PROFILING_REPORT_FAILED = -1;

// DataTypeConfig
constexpr uint64_t PROF_ACL_API              = 0x00000001ULL;
constexpr uint64_t PROF_TASK_TIME_L0         = 0x00000800ULL;
constexpr uint64_t PROF_TASK_TIME_L1         = 0x00000002ULL;
constexpr uint64_t PROF_TASK_TIME_L2         = 0x00002000ULL;
constexpr uint64_t PROF_AICORE_METRICS       = 0x00000004ULL;
constexpr uint64_t PROF_AICPU_TRACE          = 0x00000008ULL;
constexpr uint64_t PROF_L2CACHE              = 0x00000010ULL;
constexpr uint64_t PROF_HCCL_TRACE           = 0x00000020ULL;
constexpr uint64_t PROF_TRAINING_TRACE       = 0x00000040ULL;
constexpr uint64_t PROF_MSPROFTX             = 0x00000080ULL;
constexpr uint64_t PROF_RUNTIME_API          = 0x00000100ULL;
constexpr uint64_t PROF_FWK_SCHEDULE_L0      = 0x00000200ULL;
constexpr uint64_t PROF_TASK_TSFW            = 0x00000400ULL;
constexpr uint64_t PROF_TASK_TIME            = 0x00000800ULL;
constexpr uint64_t PROF_TASK_MEMORY          = 0x00001000ULL;

enum MsprofGeTaskType: int {
    MSPROF_GE_TASK_TYPE_AI_CORE = 0,
    MSPROF_GE_TASK_TYPE_AI_CPU,
    MSPROF_GE_TASK_TYPE_AIV,
    MSPROF_GE_TASK_TYPE_WRITE_BACK,
    MSPROF_GE_TASK_TYPE_MIX_AIC,
    MSPROF_GE_TASK_TYPE_MIX_AIV,
    MSPROF_GE_TASK_TYPE_FFTS_PLUS,
    MSPROF_GE_TASK_TYPE_DSA,
    MSPROF_GE_TASK_TYPE_DVPP,
    MSPROF_GE_TASK_TYPE_HCCL,
    MSPROF_GE_TASK_TYPE_INVALID
};

enum MsprofGeTensorType : int {
    MSPROF_GE_TENSOR_TYPE_INPUT = 0,
    MSPROF_GE_TENSOR_TYPE_OUTPUT,
};

struct MsProfApi {
    uint16_t magicNumber = MSPROF_REPORT_DATA_MAGIC_NUM;
    uint16_t level;
    uint32_t type;
    uint32_t threadId;
    uint32_t reserve;
    uint64_t beginTime;
    uint64_t endTime;
    uint64_t itemId;
};

struct MsprofRuntimeTrack {
    uint16_t deviceId;
    uint16_t streamId;
    uint32_t taskId;
    uint64_t taskType;
};

enum ProfCtrlType {
    PROF_CTRL_INVALID = 0,
    PROF_CTRL_SWITCH,
    PROF_CTRL_REPORTER,
    PROF_CTRL_STEPINFO,
    PROF_CTRL_BUTT
};

enum MsprofCommandHandleType {
    PROF_COMMANDHANDLE_TYPE_INIT = 0,
    PROF_COMMANDHANDLE_TYPE_START,
    PROF_COMMANDHANDLE_TYPE_STOP,
    PROF_COMMANDHANDLE_TYPE_FINALIZE,
    PROF_COMMANDHANDLE_TYPE_MODEL_SUBSCRIBE,
    PROF_COMMANDHANDLE_TYPE_MODEL_UNSUBSCRIBE,
    PROF_COMMANDHANDLE_TYPE_MAX
};

#define PATH_LEN_MAX 1023
#define PARAM_LEN_MAX 4095
struct MsprofCommandHandleParams {
    uint32_t pathLen;
    uint32_t storageLimit;  // MB
    uint32_t profDataLen;
    char path[PATH_LEN_MAX + 1];
    char profData[PARAM_LEN_MAX + 1];
};

#define MSPROF_MAX_DEV_NUM 64
struct MsprofCommandHandle {
    uint64_t profSwitch;
    uint64_t profSwitchHi;
    uint32_t devNums;
    uint32_t devIdList[MSPROF_MAX_DEV_NUM];
    uint32_t modelId;
    uint32_t type;
    struct MsprofCommandHandleParams params;
};

#pragma pack(1)
struct MsprofNodeBasicInfo {
    uint64_t opName;
    uint32_t taskType;
    uint64_t opType;
    uint32_t blockDim;
    uint32_t opFlag;
};
#pragma pack()

const uint16_t MSPROF_COMPACT_INFO_DATA_LENGTH = 40;
struct MsprofCompactInfo {
    uint16_t magicNumber = MSPROF_REPORT_DATA_MAGIC_NUM;
    uint16_t level;
    uint32_t type;
    uint32_t threadId;
    uint32_t dataLen;
    uint64_t timeStamp;
    union {
        uint8_t info[MSPROF_COMPACT_INFO_DATA_LENGTH];
        MsprofRuntimeTrack runtimeTrack;
        MsprofNodeBasicInfo nodeBasicInfo;
    } data;
};

const uint16_t MSPROF_ADDTIONAL_INFO_DATA_LENGTH = 232;
struct MsprofAdditionalInfo {  // for MsprofReportAdditionalInfo buffer data
    uint16_t magicNumber = MSPROF_REPORT_DATA_MAGIC_NUM;
    uint16_t level;
    uint32_t type;
    uint32_t threadId;
    uint32_t dataLen;
    uint64_t timeStamp;
    uint8_t  data[MSPROF_ADDTIONAL_INFO_DATA_LENGTH];
};

struct MsprofContextIdInfo {
    uint64_t opName;
    uint32_t ctxIdNum;
    uint32_t ctxIds[MSPROF_CTX_ID_MAX_NUM];
};

struct MsrofTensorData {
    uint32_t tensorType;
    uint32_t format;
    uint32_t dataType;
    uint32_t shape[MSPROF_GE_TENSOR_DATA_SHAPE_LEN];
};

struct MsprofTensorInfo {
    uint64_t opName;
    uint32_t tensorNum;
    MsrofTensorData tensorData[ATB_MSPROF_TENSOR_DATA_SIZE];
};

MSVP_PROF_API int32_t MsprofReportApi(uint32_t agingFlag, const MsProfApi *api);

MSVP_PROF_API int32_t MsprofReportCompactInfo(uint32_t agingFlag, const void* data, uint32_t length);

MSVP_PROF_API int32_t MsprofRegTypeInfo(uint16_t level, uint32_t typeId, const char *typeName);

MSVP_PROF_API int32_t MsprofReportAdditionalInfo(uint32_t agingFlag, const void* data, uint32_t length);

MSVP_PROF_API uint64_t MsprofGetHashId(const char *hashInfo, size_t length);

MSVP_PROF_API uint64_t MsprofSysCycleTime();

MSVP_PROF_API int32_t MsprofRegisterCallback(uint32_t moduleId, ProfCommandHandle handle);

#ifdef __cplusplus
}
#endif
#endif