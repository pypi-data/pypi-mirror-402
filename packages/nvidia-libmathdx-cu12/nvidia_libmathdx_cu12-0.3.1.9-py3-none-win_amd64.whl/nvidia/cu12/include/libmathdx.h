// Copyright (c) 2024-2026, NVIDIA CORPORATION & AFFILIATES.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.

// libmathdx's API is subject to change.
// Please contact Math-Libs-Feedback@nvidia.com for usage feedback.

#ifndef MATHDX_MATHDX_H
#define MATHDX_MATHDX_H

#include "libcommondx.h"

/**
 * @brief libmathdx major version number.
 */
#define LIBMATHDX_VER_MAJOR 0

/**
 * @brief libmathdx minor version number.
 */
#define LIBMATHDX_VER_MINOR 3

/**
 * @brief libmathdx patch version number.
 */
#define LIBMATHDX_VER_PATCH 1

/**
 * @brief libmathdx source commit SHA as a string.
 */
#define LIBMATHDX_COMMIT "8412a54a363b8729cd9f8de3d7fa6788c8e7b4b7"

#if defined(__cplusplus)
extern "C" {
#endif /* __cplusplus */

/**
 * @brief Returns the libmathdx version as a single integer
 *
 * @param[out] version The version, encoded as 1000 * major + 100 * minor + patch
 * @return `COMMONDX_SUCCESS`
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL mathdxGetVersion(int* version) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Returns the libmathdx version as a triplet of integers
 *
 * @param[out] major The major version.
 * @param[out] minor The minor version.
 * @param[out] patch The patch version.
 * @return `COMMONDX_SUCCESS`
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL mathdxGetVersionEx(int* major,
                                                                   int* minor,
                                                                   int* patch) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Returns the corresponding MathDx package "calver" version as a triplet of integers
 *
 * @param[out] year The year
 * @param[out] month The month
 * @param[out] patch The patch version.
 * @return `COMMONDX_SUCCESS`
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL mathdxGetPackageVersion(int* year,
                                                                        int* month,
                                                                        int* patch) LIBMATHDX_API_NOEXCEPT;

/**
 * @brief Returns the libmathdx source commit as a string.
 * This function does not allocate.
 * The returned string must not be mutated or free.
 *
 * @param[out] commit A pointer to C-string containing the library commit hash as a string.
 * @return `COMMONDX_SUCCESS`
 */
LIBMATHDX_API commondxStatusType LIBMATHDX_CALL mathdxGetCommit(const char** commit) LIBMATHDX_API_NOEXCEPT;

#if defined(__cplusplus)
} // extern "C"
#endif /* __cplusplus */

#endif // MATHDX_MATHDX_H
