cmake_minimum_required(VERSION 3.30)

set(NAME mpfr)
set(VERSION 4.2.2)
set(EXT tar.xz)
set(SHA256 b67ba0383ef7e8a8563734e2e889ef5ec3c3b898a01d00fa0a6869ad81c6ce01)

project("cmeel-${NAME}" VERSION "${VERSION}")

if(APPLE)
  set(ORIGIN "@loader_path")
  set(TEST_COMMAND
      ${CMAKE_COMMAND} "-E" "env"
      "DYLD_LIBRARY_PATH=$ENV{CMEEL_AVAILABLE_PREFIX}/lib" "--" "make" "check")
else()
  set(ORIGIN "\$\$ORIGIN")
  set(TEST_COMMAND
      ${CMAKE_COMMAND} "-E" "env"
      "LD_LIBRARY_PATH=$ENV{CMEEL_AVAILABLE_PREFIX}/lib" "--" "make" "check")
endif()

include(ExternalProject)
ExternalProject_Add(
  ${NAME}
  URL "https://www.mpfr.org/mpfr-current/${NAME}-${VERSION}.${EXT}"
  URL_HASH "SHA256=${SHA256}"
  DOWNLOAD_EXTRACT_TIMESTAMP ON
  BUILD_IN_SOURCE ON
  CONFIGURE_COMMAND
    ${CMAKE_COMMAND} "-E" "env" "LDFLAGS=-Wl,-rpath,'${ORIGIN}/../lib'" "--"
    "./configure" "--prefix=${CMAKE_INSTALL_PREFIX}"
    "--with-gmp=$ENV{CMEEL_AVAILABLE_PREFIX}"
  BUILD_COMMAND "make"
  TEST_COMMAND ${TEST_COMMAND}
  INSTALL_COMMAND "make" "install"
  COMMAND "${CMAKE_COMMAND}" "-E" "rm"
          "${CMAKE_INSTALL_PREFIX}/lib/lib${NAME}.la")

# dummy file for install target
install(FILES "README.md" DESTINATION "share/cmeel-${NAME}/")
