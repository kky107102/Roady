<template>
  <RouterView />
</template>

<style>
:root {
  font-family:
    'Noto Sans KR',
    Pretendard,
    'Malgun Gothic',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    sans-serif;
  color: #172235;
  background: #f4f7fa;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
}

* {
  box-sizing: border-box;
}

html,
body,
#app {
  min-width: 320px;
  min-height: 100%;
  margin: 0;
}

button,
input {
  font-family: inherit;
}
</style>
