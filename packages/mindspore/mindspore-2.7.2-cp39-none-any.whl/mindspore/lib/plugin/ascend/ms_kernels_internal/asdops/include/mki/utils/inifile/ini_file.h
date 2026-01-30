/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_INIFILE_INI_FILE_H
#define MKI_UTILS_INIFILE_INI_FILE_H
#include <string>
#include <map>

namespace Mki_ms {
class IniFile {
public:
    static bool ParseIniFileToMap(const std::string &iniFilePath,
        std::map<std::string, std::map<std::string, std::string>> &contentInfoMap, bool symCheck = true);
    static bool ParseIniFileToMapNoLog(const std::string &iniFilePath,
        std::map<std::string, std::map<std::string, std::string>> &contentInfoMap, bool symCheck = true);
};
} // namespace Mki_ms
#endif
