cmake_minimum_required(VERSION 3.30)

set(NAME libomp)
set(VERSION "21.1.8")
set(EXT tar.xz)
set(SHA256 4633a23617fa31a3ea51242586ea7fb1da7140e426bd62fc164261fe036aa142)

project("cmeel-${NAME}" VERSION "${VERSION}")

include(ExternalProject)
ExternalProject_Add(
  ${NAME}
  URL "https://github.com/llvm/llvm-project/releases/download/llvmorg-${VERSION}/llvm-project-${VERSION}.src.${EXT}"
  URL_HASH "SHA256=${SHA256}"
  SOURCE_SUBDIR "openmp"
  CMAKE_ARGS "-DCMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX}")

# dummy file for install target
install(FILES "README.md" DESTINATION "share/cmeel-${NAME}/")
