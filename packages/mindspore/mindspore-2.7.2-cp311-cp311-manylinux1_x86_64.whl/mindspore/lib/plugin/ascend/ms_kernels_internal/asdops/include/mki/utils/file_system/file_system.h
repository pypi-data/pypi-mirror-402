/*
 * Copyright (c) 2024 Huawei Technologies Co., Ltd.
 * This file is a part of the CANN Open Software.
 * Licensed under CANN Open Software License Agreement Version 1.0 (the "License").
 * Please refer to the License for details. You may not use this file except in compliance with the License.
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
 * See LICENSE in the root of the software repository for the full text of the License.
 */
#ifndef MKI_UTILS_FILESYSTEM_FILESYSTEM_H
#define MKI_UTILS_FILESYSTEM_FILESYSTEM_H
#include <string>
#include <vector>
#include <sys/stat.h>
namespace Mki_ms {
constexpr int64_t MAX_FILE_SIZE = 10737418240;   // 10737418240 即10GB
constexpr int64_t MAX_FILE_NUM = 100;
constexpr mode_t FILE_MODE = S_IRUSR | S_IWUSR | S_IRGRP;
class FileSystem {
public:
    static void GetDirChildItems(const std::string &dirPath, std::vector<std::string> &itemPaths);
    static void GetDirChildFiles(const std::string &dirPath, std::vector<std::string> &filePaths);
    static void GetDirChildDirs(const std::string &dirPath, std::vector<std::string> &dirPaths);
    static bool Exists(const std::string &path);
    static bool IsDir(const std::string &path);
    static std::string Join(const std::vector<std::string> &paths);
    static int64_t FileSize(const std::string &filePath);
    static std::string BaseName(const std::string &filePath);
    static std::string DirName(const std::string &path);
    static bool ReadFile(const std::string &filePath, uint8_t *buffer, uint64_t bufferSize);
    static bool WriteFile(const char *codeBuf, uint64_t codeLen, const std::string &filePath,
                          const mode_t mode = FILE_MODE);
    static void DeleteFile(const std::string &filePath);
    static bool Rename(const std::string &filePath, const std::string &newFilePath);
    static bool MakeDir(const std::string &dirPath, int mode);
    static bool Makedirs(const std::string &dirPath, const mode_t mode);
    static std::string PathCheckAndRegular(const std::string &path, bool symlinkCheck = true,
                                           bool parentReferenceCheck = true);
    static std::string PathCheckAndRegularNoLog(const std::string &path, bool symlinkCheck = true,
                                           bool parentReferenceCheck = true);

private:
    // A symlink with a trailing slash (/) is not recognized as a symlink,
    // which is consistent with the operating system.
    static bool IsSymLink(const std::string &filePath);
    static std::string RemoveTrailingSlash(const std::string &path);
    static void GetDirChildItemsImpl(const std::string &dirPath, bool matchFile, bool matchDir,
                                     std::vector<std::string> &itemPaths);
};
} // namespace Mki_ms
#endif
