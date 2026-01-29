cmake_minimum_required(VERSION 3.30)

set(ORG KarypisLab)
set(NAME METIS)
set(VERSION 5.2.1)
set(EXT tar.gz)
set(SHA256 1a4665b2cd07edc2f734e30d7460afb19c1217c2547c2ac7bf6e1848d50aff7a)
set(TAG_PREFIX refs/tags/v)

project("cmeel-${NAME}" VERSION "${VERSION}")

if(APPLE)
  set(ORIGIN "@loader_path")
else()
  set(ORIGIN "\$\$ORIGIN")
endif()

include(ExternalProject)
ExternalProject_Add(
  ${NAME}
  URL "https://github.com/${ORG}/${NAME}/archive/${TAG_PREFIX}${VERSION}.${EXT}"
  URL_HASH "SHA256=${SHA256}"
  DOWNLOAD_EXTRACT_TIMESTAMP OFF
  BUILD_IN_SOURCE ON
  PATCH_COMMAND
    "sh" "-c"
    "sed -i.bak 's/VERSION 2.8/VERSION 3.10/' CMakeLists.txt && echo 'target_link_libraries(metis PUBLIC GKlib)' >> libmetis/CMakeLists.txt"
  CONFIGURE_COMMAND
    ${CMAKE_COMMAND} "-E" "env" "LDFLAGS=-Wl,-rpath,'${ORIGIN}/../lib'" "--"
    "make" "config" "shared=1" "prefix=${CMAKE_INSTALL_PREFIX}"
    "gklib_path=$ENV{CMEEL_AVAILABLE_PREFIX}"
  BUILD_COMMAND "make" "-i"
  INSTALL_COMMAND "make" "install" "-i")

# dummy file for install target
install(FILES "README.md" DESTINATION "share/cmeel-${NAME}/")
