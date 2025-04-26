<template>
  <div class="container">
    <!-- 左侧文件列表 -->
    <div class="sidebar" :style="{ width: sidebarWidth + 'px' }">
      <div class="resize-handle vertical" @mousedown="handleResizeStart($event, 'sidebar')"></div>
      <el-scrollbar>
        <div class="button-group">
        <el-upload
          class="upload-demo"
          action="#"
          :auto-upload="false"
          :on-change="handleFileChange"
          :file-list="fileList"
          multiple>
          <template #trigger>
              <el-button type="primary" class="action-button">选择文件</el-button>
          </template>
          </el-upload>
          <el-button 
            type="success" 
            class="action-button"
            @click="uploadFile">
            上传文件
          </el-button>
          <el-button 
            type="warning" 
            class="action-button"
            @click="handleMergePoints"
            :disabled="!allWaypoints.length">
            合并航点
          </el-button>

          <el-button 
            type="primary" 
            class="action-button"
            @click="handleOffsetPoints"
            :disabled="!allWaypoints.length">
            偏移量设置
          </el-button>
          
          <el-button 
            type="warning" 
            class="action-button"
            @click="handleCheckAbnormalPoints"
            :disabled="!allWaypoints.length">
            异常点排查
          </el-button>

          <el-button 
            type="danger" 
            class="action-button"
            @click="handleDeleteAbnormalPoints"
            :disabled="!allWaypoints.length || abnormalPoints.size === 0">
            删除异常点
          </el-button>
          <el-button 
            type="danger" 
            class="action-button"
            @click="handleBoxSelect"
            :disabled="!allWaypoints.length">
            框选删除
          </el-button>
          
          <el-button 
            type="primary" 
            class="action-button"
            @click="handleSplitPoints"
            :disabled="!isMerged || !allWaypoints.length">
            切割航点
          </el-button>
          <el-button 
            type="success" 
            class="action-button"
            @click="handleExport"
            :disabled="!allWaypoints.length">
            导出航点
          </el-button>

        </div>
        
        <div class="file-list">
          <h3>已上传文件</h3>
          <el-scrollbar height="calc(100% - 180px)">
            <div v-if="fileList.length" class="file-items">
              <div 
                v-for="file in fileList" 
                :key="file.name"
                class="file-item"
                :class="{ 'active': activeFile === file.name }">
                <div class="file-content" @click="handleFileClick(file)">
                <div class="file-header">
                  <el-icon><Document /></el-icon>
                  <span class="file-name" :style="{ color: getFileColor(file.name) }">
                    {{ file.name }}
                  </span>
                </div>
                <div class="file-stats">
                  <div class="stat-item">
                    <span class="stat-label">航点：</span>
                    <span class="stat-value">{{ getFileStats(file.name).waypointCount }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">有效点：</span>
                    <span class="stat-value">{{ getFileStats(file.name).validCount }}</span>
                  </div>
                  </div>
                </div>
                <div class="file-actions">
                  <el-button 
                    type="danger" 
                    link
                    size="small"
                    @click.stop="handleDeleteFile(file.name)">
                    删除
                  </el-button>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无文件" />
          </el-scrollbar>
        </div>
      </el-scrollbar>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
      <!-- 地图容器 -->
      <div id="map" ref="mapContainer" :style="{ height: mapHeight + 'px' }">
        <div class="resize-handle horizontal" @mousedown="handleResizeStart($event, 'map')"></div>
      </div>
      
      <!-- 数据表格 -->
      <div class="data-table" :style="{ height: tableHeight + 'px' }">
        <el-tabs v-model="activeTab" class="demo-tabs">
          <el-tab-pane label="航点列表" name="waypoints">
            <div class="table-container">
              <el-table 
                :data="waypoints"
                @row-click="handleRowClick"
                :max-height="tableHeight - 70"
                :row-style="getRowStyle">
                <el-table-column prop="index" label="序号" width="80" />
                <el-table-column prop="fileName" label="文件名" width="180" />
                <el-table-column prop="mode" label="模式" width="80">
                  <template #default="scope">
                    {{ getModeText(scope.row.mode) }}
                  </template>
                </el-table-column>
                <el-table-column prop="function" label="功能" width="100">
                  <template #default="scope">
                    {{ getFunctionText(scope.row.function) }}
                  </template>
                </el-table-column>
                <el-table-column prop="latitude" label="纬度" width="120" />
                <el-table-column prop="longitude" label="经度" width="120" />
                <el-table-column prop="altitude" label="高度" width="100" />
                <el-table-column label="参数" width="200">
                  <template #default="scope">
                    {{ scope.row.params.join(', ') }}
                  </template>
                </el-table-column>
                <el-table-column prop="inWorkArea" label="作业区" width="80">
                  <template #default="scope">
                    <el-tag 
                      :type="scope.row.inWorkArea ? 'success' : 'info'" 
                      size="small">
                      {{ scope.row.inWorkArea ? '是' : '否' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="pointType" label="点类型" width="100">
                  <template #default="scope">
                    <el-tag
                      :type="scope.row.pointType === 'entry' ? 'success' : 
                             scope.row.pointType === 'exit' ? 'danger' : 
                             abnormalPoints.has(`${scope.row.fileIndex}-${scope.row.index}`) ? 'warning' :
                             'info'"
                      size="small">
                      {{ abnormalPoints.has(`${scope.row.fileIndex}-${scope.row.index}`) ? '异常点' : getPointTypeText(scope.row.pointType) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="160" fixed="right">
                  <template #default="scope">
                    <el-button 
                      type="primary" 
                      link
                      @click.stop="handleInsertPoint(scope.row)">
                      插入
                    </el-button>
                    <el-button 
                      type="danger" 
                      link
                      @click.stop="handleDeletePoint(scope.row)">
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 添加加载状态 -->
    <el-loading 
      :visible="loading" 
      text="正在处理数据..."
      background="rgba(255, 255, 255, 0.8)"
    />

    <!-- 添加插入航点对话框 -->
    <el-dialog
      v-model="insertDialogVisible"
      title="插入航点"
      width="500px"
      :close-on-click-modal="false"
      @close="handleInsertDialogClose">
      <div class="insert-point-form">
        <el-form :model="insertForm" label-width="100px">
          <el-form-item label="插入位置">
            <el-input-number 
              v-model="insertForm.index" 
              :min="1" 
              :max="maxInsertIndex"
              controls-position="right" />
          </el-form-item>
          <el-form-item label="选择方式">
            <el-radio-group 
              v-model="insertForm.inputMethod"
              @change="handleInputMethodChange">
              <el-radio label="map">地图选点</el-radio>
              <el-radio label="manual">手动输入</el-radio>
            </el-radio-group>
          </el-form-item>
          <template v-if="insertForm.inputMethod === 'manual'">
            <el-form-item label="纬度">
              <el-input v-model.number="insertForm.latitude" type="number" />
            </el-form-item>
            <el-form-item label="经度">
              <el-input v-model.number="insertForm.longitude" type="number" />
            </el-form-item>
            <el-form-item label="高度">
              <el-input v-model.number="insertForm.altitude" type="number" />
            </el-form-item>
          </template>
          <template v-else>
            <el-form-item>
              <div class="map-select-container">
                <div v-if="!isSelectingPoint" class="map-tip">
                  <div class="selected-point-info" v-if="tempMarker">
                    <div class="coords-display">
                      <div class="coord-item">
                        <span class="coord-label">纬度:</span>
                        <el-input 
                          v-model.number="insertForm.latitude" 
                          type="number" 
                          size="small"
                          :step="0.000001"
                          @change="updateMarkerPosition" />
                      </div>
                      <div class="coord-item">
                        <span class="coord-label">经度:</span>
                        <el-input 
                          v-model.number="insertForm.longitude" 
                          type="number"
                          size="small"
                          :step="0.000001"
                          @change="updateMarkerPosition" />
                      </div>
                      <div class="coord-item">
                        <span class="coord-label">高度:</span>
                        <el-input 
                          v-model.number="insertForm.altitude" 
                          type="number"
                          size="small" />
                      </div>
                    </div>
                  </div>
                  <el-button type="primary" @click="startSelectPoint">
                    {{ tempMarker ? '重新选点' : '开始选点' }}
                  </el-button>
                </div>
                <div v-else class="map-tip selecting">
                  <el-alert
                    title="请在地图上点击选择位置"
                    type="info"
                    :closable="false">
                    <template #default>
                      点击地图选择位置，选点完成后可以拖动调整位置或直接编辑坐标
                    </template>
                  </el-alert>
                  <el-button type="primary" @click="finishSelectPoint">
                    完成选点
                  </el-button>
                </div>
              </div>
            </el-form-item>
          </template>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleInsertDialogClose">取消</el-button>
          <el-button type="primary" @click="confirmInsertPoint" :disabled="!canInsert">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加偏移量设置对话框 -->
    <el-dialog
      v-model="offsetDialogVisible"
      title="设置航点偏移量"
      width="400px"
      :close-on-click-modal="false"
      @close="handleOffsetDialogClose">
      <div class="offset-form">
        <el-form :model="offsetForm" label-width="120px">
          <el-form-item label="经度偏移(cm)">
            <el-input-number 
              v-model="offsetForm.longitudeOffset" 
              :precision="2"
              :step="1"
              controls-position="right" />
          </el-form-item>
          <el-form-item label="纬度偏移(cm)">
            <el-input-number 
              v-model="offsetForm.latitudeOffset" 
              :precision="2"
              :step="1"
              controls-position="right" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleOffsetDialogClose">取消</el-button>
          <el-button type="primary" @click="confirmOffsetPoints">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import mapboxgl from 'mapbox-gl'
import { onMounted, ref, onUnmounted, computed, nextTick } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document } from '@element-plus/icons-vue'
import MapboxDraw from '@mapbox/mapbox-gl-draw'
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css'
import arrowIcon from '@/assets/arrow.png?base64'
import * as turf from '@turf/turf'

export default {
  name: 'MapComponent',
  components: {
    Document
  },
  setup() {
    const mapContainer = ref(null)
    const fileList = ref([])
    const allWaypoints = ref([])
    const markerColors = [
      '#FF0000', // 红色
      '#0000FF', // 蓝色
      '#00FF00', // 绿色
      '#FFA500', // 橙色
      '#800080', // 紫色
      '#00FFFF', // 青色
      '#FF00FF', // 品红
      '#FFD700'  // 金色
    ]
    const activeTab = ref('waypoints')
    let map = null
    const activeFile = ref(null)

    // 修改初始尺寸
    const sidebarWidth = ref(350) // 增加侧边栏宽度
    const mapHeight = ref(window.innerHeight * 0.65) // 调整地图高度比例
    const tableHeight = ref(window.innerHeight * 0.35 - 50) // 调整表格高度比例
    let isResizing = false
    let currentResizeTarget = null
    let startX = 0
    let startY = 0
    let startWidth = 0
    let startHeight = 0

    // 修改标记存储结构
    const pointsData = ref({
      type: 'FeatureCollection',
      features: []
    })
    const activePointId = ref(null)

    // 添加加载状态
    const loading = ref(false)

    // 插入航点相关状态
    const insertDialogVisible = ref(false)
    const insertForm = ref({
      index: 1,
      inputMethod: 'map',
      latitude: null,
      longitude: null,
      altitude: 0,
      fileIndex: null,
      fileName: null,
      sourcePoint: null
    })
    const tempMarker = ref(null)
    const currentInsertFile = ref(null)

    // 添加选点状态
    const isSelectingPoint = ref(false)

    // 添加作业区相关状态
    const draw = ref(null)
    const workAreas = ref([]) // 存储所有作业区

    // 在 setup 函数中添加状态
    const POINT_TYPES = {
      NORMAL: 'normal',
      ENTRY: 'entry',    // 驶入点
      EXIT: 'exit'       // 驶出点
    }

    // 在 setup 函数中添加合并状态
    const isMerged = ref(false)

    // 添加切割相关的状态和函数
    const splitForm = ref({
      maxPoints: 4000
    })

    // 添加一个状态标记是否处于插入模式
    const isInInsertMode = ref(false)

    // 添加异常点状态
    const abnormalPoints = ref(new Set())

    // 在 setup 函数中添加新的状态
    const isBoxSelecting = ref(false)
    const selectedPoints = ref(new Set())

    const handleFileChange = (uploadFile) => {
      // 检查是否存在同名文件
      const existingFileIndex = fileList.value.findIndex(f => f.name === uploadFile.name)
      if (existingFileIndex !== -1) {
        // 提示用户是否覆盖
        ElMessageBox.confirm(
          `文件 "${uploadFile.name}" 已存在，是否覆盖？`,
          '提示',
          {
            confirmButtonText: '覆盖',
            cancelButtonText: '取消',
            type: 'warning'
          }
        ).then(() => {
          // 删除旧文件相关数据
          removeFileData(uploadFile.name)
          // 替换文件列表中的文件
          fileList.value.splice(existingFileIndex, 1, uploadFile)
        }).catch(() => {
          // 用户取消覆盖，移除新上传的文件
          fileList.value = fileList.value.filter(f => f.name !== uploadFile.name)
        })
      } else {
        // 新文件直接添加
        fileList.value.push(uploadFile)
      }
    }

    // 添加文件删除功能
    const handleDeleteFile = (fileName) => {
      ElMessageBox.confirm(
        `确定要删除文件 "${fileName}" 吗？`,
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        removeFileData(fileName)
        ElMessage.success('文件删除成功')
      }).catch(() => {
        // 用户取消删除
      })
    }

    // 添加文件数据清理函数
    const removeFileData = (fileName) => {
      // 从文件列表中移除
      fileList.value = fileList.value.filter(f => f.name !== fileName)
      
      // 从航点数据中移除
      allWaypoints.value = allWaypoints.value.filter(p => p.fileName !== fileName)
      
      // 从地图点位中移除
      pointsData.value.features = pointsData.value.features.filter(
        f => f.properties.fileName !== fileName
      )
      
      // 更新地图显示
      updatePointsLayer()
      updateLinesLayer()
      
      // 如果删除的是当前活动文件，清除活动状态
      if (activeFile.value === fileName) {
        activeFile.value = null
      }
    }

    // 添加经纬度验证函数
    const isValidCoordinate = (lat, lng) => {
      return lat && lng && 
             !isNaN(lat) && !isNaN(lng) && 
             lat !== 0 && lng !== 0 && 
             Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
    }

    // 添加点位到地图
    const addPoints = (points, fileIndex, fileName, color) => {
      points.forEach(point => {
        const feature = {
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: [point.longitude, point.latitude]
            },
            properties: {
            id: `${fileIndex}-${point.index}`,
            fileIndex: fileIndex,
              pointIndex: point.index,
            fileName: fileName,
            color: color,
            description: `${fileName}<br>航点 ${point.index}`,
            inWorkArea: false,
            pointType: 'normal',
            isActive: fileName === activeFile.value  // 添加活动状态属性
          }
        }

        pointsData.value.features.push(feature)
      })

      updatePointsLayer()
    }

    // 更新点图层
    const updatePointsLayer = () => {
      const layerStyle = {
            'circle-radius': [
              'case',
          ['in', ['get', 'id'], ['literal', Array.from(selectedPoints.value)]], 12, // 选中的点更大
          ['in', ['get', 'id'], ['literal', Array.from(abnormalPoints.value)]], 12,
          ['==', ['get', 'pointType'], POINT_TYPES.ENTRY], 12,
          ['==', ['get', 'pointType'], POINT_TYPES.EXIT], 12,
          8
        ],
        'circle-color': [
          'case',
          ['in', ['get', 'id'], ['literal', Array.from(selectedPoints.value)]], '#FF0000', // 选中的点显示红色
          ['in', ['get', 'id'], ['literal', Array.from(abnormalPoints.value)]], '#FF00FF',
          ['==', ['get', 'pointType'], POINT_TYPES.ENTRY], '#67C23A',
          ['==', ['get', 'pointType'], POINT_TYPES.EXIT], '#F56C6C',
          ['get', 'color']
        ],
            'circle-opacity': [
              'case',
          ['in', ['get', 'id'], ['literal', Array.from(selectedPoints.value)]], 1,
          ['in', ['get', 'id'], ['literal', Array.from(abnormalPoints.value)]], 1,
          ['==', ['get', 'isActive'], true], 1,
          ['==', ['get', 'id'], activePointId.value], 1,
          0.6
            ],
            'circle-stroke-width': [
              'case',
          ['in', ['get', 'id'], ['literal', Array.from(selectedPoints.value)]], 3,
          ['in', ['get', 'id'], ['literal', Array.from(abnormalPoints.value)]], 3,
          ['==', ['get', 'id'], activePointId.value], 3,
          ['==', ['get', 'isActive'], true], 2,
          1
            ],
            'circle-stroke-color': [
              'case',
          ['in', ['get', 'id'], ['literal', Array.from(selectedPoints.value)]], '#FFFF00',
          ['in', ['get', 'id'], ['literal', Array.from(abnormalPoints.value)]], '#FFFF00',
              ['==', ['get', 'id'], activePointId.value], '#ffff00',
          ['==', ['get', 'isActive'], true], '#ffffff',
          'rgba(255, 255, 255, 0.6)'
        ]
      }

      if (!map.getSource('points')) {
        map.addSource('points', {
          type: 'geojson',
          data: pointsData.value
        })

        map.addLayer({
          id: 'points-circle',
          type: 'circle',
          source: 'points',
          paint: layerStyle
        })

        // 添加拖动状态变量
        let isDragging = false
        let draggedPoint = null
        let originalPosition = null

        // 添加鼠标按下事件
        map.on('mousedown', 'points-circle', (e) => {
          if (isInInsertMode.value) return // 插入模式下禁用拖动
          
          if (e.features.length > 0) {
            isDragging = true
            draggedPoint = e.features[0]
            originalPosition = [...draggedPoint.geometry.coordinates]
            
            // 修改鼠标样式
            map.getCanvas().style.cursor = 'grabbing'
            
            // 阻止事件冒泡
            e.preventDefault()
          }
        })

        // 添加鼠标移动事件
        map.on('mousemove', (e) => {
          if (!isDragging) return

          // 更新点位置
          const features = pointsData.value.features.map(feature => {
            if (feature.properties.id === draggedPoint.properties.id) {
              return {
                ...feature,
                geometry: {
                  ...feature.geometry,
                  coordinates: [e.lngLat.lng, e.lngLat.lat]
                }
              }
            }
            return feature
          })
          
          pointsData.value.features = features
        map.getSource('points').setData(pointsData.value)
        })

        // 添加鼠标松开事件
        map.on('mouseup', () => {
          if (!isDragging) return

          const newPosition = pointsData.value.features.find(
            f => f.properties.id === draggedPoint.properties.id
          ).geometry.coordinates

          // 恢复鼠标样式
          map.getCanvas().style.cursor = ''

          // 询问用户是否确认更新位置
          ElMessageBox.confirm(
            `是否确认更新航点位置？\n` +
            `原位置：${originalPosition[1].toFixed(8)}, ${originalPosition[0].toFixed(8)}\n` +
            `新位置：${newPosition[1].toFixed(8)}, ${newPosition[0].toFixed(8)}`,
            '确认更新',
            {
              confirmButtonText: '确认',
              cancelButtonText: '取消',
              type: 'warning'
            }
          ).then(() => {
            // 用户确认，更新点位数据
            const point = allWaypoints.value.find(p => 
              p.fileIndex === draggedPoint.properties.fileIndex && 
              p.index === draggedPoint.properties.pointIndex
            )
            
            if (point) {
              point.latitude = Number(newPosition[1].toFixed(8))
              point.longitude = Number(newPosition[0].toFixed(8))
              
              // 更新作业区状态
              if (workAreas.value.length > 0) {
                const isInWorkArea = workAreas.value.some(area => 
                  isPointInPolygon([newPosition[0], newPosition[1]], area)
                )
                point.inWorkArea = isInWorkArea
                
                // 更新点位类型
                updateWorkAreaPoints()
              }

              // 触发表格更新
              allWaypoints.value = [...allWaypoints.value]
              
              ElMessage.success('航点位置已更新')
            }
          }).catch(() => {
            // 用户取消，恢复原位置
            pointsData.value.features = pointsData.value.features.map(feature => {
              if (feature.properties.id === draggedPoint.properties.id) {
                return {
                  ...feature,
                  geometry: {
                    ...feature.geometry,
                    coordinates: originalPosition
                  }
                }
              }
              return feature
            })
            map.getSource('points').setData(pointsData.value)
          }).finally(() => {
            // 重置拖动状态
            isDragging = false
            draggedPoint = null
            originalPosition = null
          })
        })

        // 修改鼠标悬停事件
        map.on('mouseenter', 'points-circle', () => {
          if (!isInInsertMode.value) {
            map.getCanvas().style.cursor = isDragging ? 'grabbing' : 'grab'
          }
        })

        map.on('mouseleave', 'points-circle', () => {
          if (!isInInsertMode.value && !isDragging) {
            map.getCanvas().style.cursor = ''
          }
        })

        // 修改点击事件处理
        map.on('click', 'points-circle', (e) => {
          if (isInInsertMode.value) return // 插入模式下不处理点击
          
          if (e.features.length > 0) {
            const feature = e.features[0]
            const { fileIndex, pointIndex, fileName } = feature.properties

            // 高亮显示点
            highlightPoint(feature.properties.id)

            // 定位到表格对应行
            const point = allWaypoints.value.find(p => 
              p.fileIndex === fileIndex && 
              p.index === pointIndex &&
              p.fileName === fileName
            )

            if (point) {
              // 获取表格实例
              const tableRef = document.querySelector('.el-table__body-wrapper')
              if (tableRef) {
                // 找到目标行元素
                const rows = tableRef.querySelectorAll('.el-table__row')
                const targetElement = Array.from(rows).find(row => {
                  const cells = row.querySelectorAll('td')
                  return parseInt(cells[0].textContent) === point.index && 
                         cells[1].textContent === point.fileName
                })

                if (targetElement) {
                  // 移除其他行的高亮
                  rows.forEach(row => row.classList.remove('highlight-row'))
                  // 高亮当前行
                  targetElement.classList.add('highlight-row')
                  
                  // 滚动到目标行
                  targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                  })
                }
              }
            }

            // 显示弹出框
            new mapboxgl.Popup()
              .setLngLat(feature.geometry.coordinates)
              .setHTML(`${fileName}<br>航点 ${pointIndex}`)
              .addTo(map)
          }
        })
      } else {
        // 更新数据源
        map.getSource('points').setData(pointsData.value)
        
        // 更新样式
        Object.entries(layerStyle).forEach(([property, value]) => {
          map.setPaintProperty('points-circle', property, value)
        })
      }
    }

    // 高亮显示点
    const highlightPoint = (pointId) => {
      // 更新活动点ID
      activePointId.value = pointId
      
      // 更新点图层样式
      if (map && map.getSource('points')) {
        updatePointsLayer()
      }
    }

    // 定位到表格行
    const scrollToTableRow = (fileIndex, pointIndex) => {
      // 找到对应的行
      const targetRow = allWaypoints.value.find(
        point => point.fileIndex === fileIndex && point.index === pointIndex
      )
      
      if (targetRow) {
        // 获取表格实例
        const tableRef = document.querySelector('.el-table__body-wrapper')
        if (!tableRef) return

        // 找到目标行元素
        const rows = tableRef.querySelectorAll('.el-table__row')
        const targetElement = Array.from(rows).find(row => {
          const cells = row.querySelectorAll('td')
          return parseInt(cells[0].textContent) === targetRow.index && 
                 cells[1].textContent === targetRow.fileName
        })

        if (targetElement) {
          // 移除其他行的高亮
        rows.forEach(row => row.classList.remove('highlight-row'))
          // 高亮当前行
          targetElement.classList.add('highlight-row')
          
          // 滚动到目标行
          targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
          })
        }
      }
    }

    // 修改文件上传处理函数
    const uploadFile = async () => {
      if (!fileList.value.length) {
        ElMessage.warning('请先选择文件')
        return
      }

      loading.value = true
      const uploadPromises = []
      const newPoints = []

      try {
        // 先处理所有文件
        for (let i = 0; i < fileList.value.length; i++) {
          const file = fileList.value[i]
          if (file.status === 'ready') {
          const formData = new FormData()
          formData.append('file', file.raw)

            const promise = axios.post('http://121.40.132.51:5005/api/waypoints', formData)
              .then(response => {
                const points = response.data.waypoints
                const color = markerColors[i % markerColors.length]
                
                // 先收集所有点，不急着添加
                points.forEach(point => {
                  newPoints.push({
                    ...point,
                    fileIndex: i,
              fileName: file.name,
                    color,
                    inWorkArea: false,
                    pointType: 'normal'
                  })
                })
                
                file.status = 'success'
              })
            uploadPromises.push(promise)
          }
        }

        // 等待所有文件处理完成
        await Promise.all(uploadPromises)

        // 获取当前最大序号
        const currentMaxIndex = allWaypoints.value.length > 0 
          ? Math.max(...allWaypoints.value.map(p => p.index))
          : 0

        // 为新点分配序号
        newPoints.forEach((point, idx) => {
          point.index = currentMaxIndex + idx + 1
        })

        // 添加新点到总列表
        allWaypoints.value = [...allWaypoints.value, ...newPoints]

        // 更新地图显示
        newPoints.forEach(point => {
          addPoints([point], point.fileIndex, point.fileName, point.color)
        })

        // 更新文件统计信息
        fileList.value.forEach(file => {
          file.stats = getFileStats(file.name)
        })

        ElMessage.success('文件上传成功')
      } catch (error) {
        console.error('Upload error:', error)
        ElMessage.error('上传失败：' + error.message)
      } finally {
        loading.value = false
      }
    }

    const getModeText = (mode) => {
      const modes = {
        0: '绝对',
        3: '相对',
        10: '地形'
      }
      return modes[mode] || mode
    }

    const getFunctionText = (func) => {
      const functions = {
        16: '航点',
        181: '继电器',
        93: '延时'
      }
      return functions[func] || func
    }

    const handleResizeStart = (e, target) => {
      e.preventDefault()
      isResizing = true
      currentResizeTarget = target
      startX = e.clientX
      startY = e.clientY
      
      if (target === 'sidebar') {
        startWidth = sidebarWidth.value
      } else if (target === 'map') {
        startHeight = mapHeight.value
      }

      document.addEventListener('mousemove', handleResize)
      document.addEventListener('mouseup', stopResize)
    }

    const handleResize = (e) => {
      if (!isResizing) return

      if (currentResizeTarget === 'sidebar') {
        const diff = e.clientX - startX
        const newWidth = startWidth + diff
        // 调整最小和最大宽度
        sidebarWidth.value = Math.max(280, Math.min(newWidth, window.innerWidth * 0.3))
      } else if (currentResizeTarget === 'map') {
        const diff = e.clientY - startY
        const newHeight = startHeight + diff
        const minHeight = window.innerHeight * 0.4 // 最小40%
        const maxHeight = window.innerHeight * 0.8 // 最大80%
        mapHeight.value = Math.max(minHeight, Math.min(newHeight, maxHeight))
        tableHeight.value = window.innerHeight - mapHeight.value - 50
      }

      if (map) {
        map.resize()
      }
    }

    const stopResize = () => {
      isResizing = false
      currentResizeTarget = null
      document.removeEventListener('mousemove', handleResize)
      document.removeEventListener('mouseup', stopResize)
    }

    // 修改文件点击处理函数
    const handleFileClick = (file) => {
      activeFile.value = file.name
      
      // 高亮显示当前文件的点位，但不隐藏其他点位
      pointsData.value.features.forEach(feature => {
        if (feature.properties.fileName === file.name) {
          feature.properties.isActive = true
        } else {
          feature.properties.isActive = false
        }
      })

      // 更新点图层样式
      updatePointsLayer()
      updateLinesLayer()
    }

    // 修改表格行点击处理函数
    const handleRowClick = (row) => {
      if (!isValidCoordinate(row.latitude, row.longitude)) {
        ElMessage.warning('该记录没有有效的坐标信息')
        return
      }

      // 生成点ID
      const pointId = `${row.fileIndex}-${row.index}`
      
      // 高亮显示点
      highlightPoint(pointId)

      // 地图定位
      const point = pointsData.value.features.find(f => 
        f.properties.id === pointId
      )

      if (point) {
        // 飞行到目标点
        map.flyTo({
          center: point.geometry.coordinates,
          zoom: 21,
          duration: 1000
        })

        // 显示弹出框
        new mapboxgl.Popup()
          .setLngLat(point.geometry.coordinates)
          .setHTML(`${row.fileName}<br>航点 ${row.index}`)
          .addTo(map)
      }
    }

    // 修改表格行样式方法
    const getRowStyle = (row) => {
      return {
        borderLeft: `4px solid ${row.color || 'transparent'}`
      }
    }

    // 获取文件颜色
    const getFileColor = (fileName) => {
      const fileData = allWaypoints.value
        .find(point => point.fileName === fileName)
      return fileData?.color || '#909399'
    }

    // 获取文件统计信息
    const getFileStats = (fileName) => {
      const waypoints = allWaypoints.value
        .filter(point => point.fileName === fileName)

      return {
        waypointCount: waypoints.length,
        validCount: waypoints.length
      }
    }

    // 添加回计算属性
    const waypoints = computed(() => {
      return allWaypoints.value.map(point => ({
        ...point,
        fileName: point.fileName || '未知文件'
      }))
    })

    // 修改删除点位函数
    const handleDeletePoint = (row) => {
      ElMessageBox.confirm(
        '确定要删除这条数据吗？',
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        // 获取同一文件中的所有点
        const sameFilePoints = allWaypoints.value.filter(
          p => p.fileName === row.fileName
        )
        
        // 删除当前点
          allWaypoints.value = allWaypoints.value.filter(
          p => !(p.fileName === row.fileName && p.index === row.index)
          )

        // 更新后续点的索引
        allWaypoints.value = allWaypoints.value.map(point => {
          if (point.fileName === row.fileName && point.index > row.index) {
            return { ...point, index: point.index - 1 }
        }
          return point
        })

        // 更新地图点位数据
        pointsData.value.features = pointsData.value.features.filter(
          f => !(f.properties.fileName === row.fileName && 
                f.properties.pointIndex === row.index)
        )
        
        // 更新剩余点位的索引和属性
        pointsData.value.features = pointsData.value.features.map(feature => {
          if (feature.properties.fileName === row.fileName && 
              feature.properties.pointIndex > row.index) {
            const newIndex = feature.properties.pointIndex - 1
            return {
              ...feature,
              properties: {
                ...feature.properties,
                pointIndex: newIndex,
                id: `${feature.properties.fileIndex}-${newIndex}`,
                description: `${feature.properties.fileName}<br>航点 ${newIndex}`
              }
            }
          }
          return feature
        })

        // 重新排序点位
        pointsData.value.features.sort((a, b) => {
          if (a.properties.fileName !== b.properties.fileName) {
            return a.properties.fileName.localeCompare(b.properties.fileName)
          }
          return a.properties.pointIndex - b.properties.pointIndex
        })

        // 更新地图显示
        updatePointsLayer()
        updateLinesLayer()

        // 更新作业区状态
        if (workAreas.value.length > 0) {
          pointsData.value.features.forEach(point => {
            const isInWorkArea = workAreas.value.some(area => 
              isPointInPolygon(
                [point.geometry.coordinates[0], point.geometry.coordinates[1]], 
                area
              )
            )
            point.properties.inWorkArea = isInWorkArea

            // 更新对应的航点数据
            const waypoint = allWaypoints.value.find(w => 
              w.fileIndex === point.properties.fileIndex && 
              w.index === point.properties.pointIndex
            )
            if (waypoint) {
              waypoint.inWorkArea = isInWorkArea
            }
          })

          // 更新驶入点和驶出点
          updateWorkAreaPoints()
        }

        // 更新文件统计
        const file = fileList.value.find(f => f.name === row.fileName)
        if (file) {
          file.stats = getFileStats(file.name)
        }

        ElMessage.success('删除成功')
      }).catch(() => {})
    }

    // 添加更新作业区点位类型的函数
    const updateWorkAreaPoints = () => {
      // 按文件分组处理点位
      const fileGroups = {}
      pointsData.value.features.forEach(point => {
        const fileName = point.properties.fileName
        if (!fileGroups[fileName]) {
          fileGroups[fileName] = []
        }
        fileGroups[fileName].push(point)
      })

      // 处理每个文件的点位
      Object.values(fileGroups).forEach(filePoints => {
        // 按索引排序
        filePoints.sort((a, b) => a.properties.pointIndex - b.properties.pointIndex)
        
        // 判断每个点的类型
        filePoints.forEach((point, index) => {
          const prevPoint = index > 0 ? filePoints[index - 1] : null
          const nextPoint = index < filePoints.length - 1 ? filePoints[index + 1] : null
          
          const isInArea = point.properties.inWorkArea
          const prevInArea = prevPoint ? prevPoint.properties.inWorkArea : false
          const nextInArea = nextPoint ? nextPoint.properties.inWorkArea : isInArea

          // 判断点的类型
          let pointType = POINT_TYPES.NORMAL
          if (!prevInArea && isInArea) {
            pointType = POINT_TYPES.ENTRY
          } else if (isInArea && !nextInArea) {
            pointType = POINT_TYPES.EXIT
          }

          // 更新点的类型
          point.properties.pointType = pointType

          // 更新对应的航点数据
          const waypoint = allWaypoints.value.find(w => 
            w.fileIndex === point.properties.fileIndex && 
            w.index === point.properties.pointIndex
          )
          if (waypoint) {
            waypoint.pointType = pointType
          }
        })
      })

      // 更新地图显示
      updatePointsLayer()

      // 触发表格更新
      allWaypoints.value = [...allWaypoints.value]
    }

    // 计算最大可插入索引
    const maxInsertIndex = computed(() => {
      if (!currentInsertFile.value) return 1
      return allWaypoints.value.filter(p => p.fileName === currentInsertFile.value).length + 1
    })

    // 判断是否可以插入
    const canInsert = computed(() => {
      if (insertForm.value.inputMethod === 'manual') {
        return isValidCoordinate(insertForm.value.latitude, insertForm.value.longitude)
      } else {
        return tempMarker.value !== null
      }
    })

    // 修改插入航点相关函数
    const handleInsertPoint = (row) => {
      // 记录当前点的信息
      insertForm.value = {
        index: row.index,
        inputMethod: 'map',
        latitude: null,
        longitude: null,
        altitude: row.altitude,
        fileIndex: row.fileIndex,
        fileName: row.fileName,
        sourcePoint: row // 保存源点信息
      }
      currentInsertFile.value = row.fileName

      // 启用地图选点模式
      enableMapSelection()
      
      // 提示用户在地图上选点
      ElMessage({
        message: '请在地图上选择插入点的位置',
        type: 'info',
        duration: 0,
        showClose: true
      })
    }

    // 修改地图选点相关函数
    const enableMapSelection = () => {
      // 设置插入模式状态
      isInInsertMode.value = true
      
      // 移除之前的临时标记
      if (tempMarker.value) {
        tempMarker.value.remove()
        tempMarker.value = null
      }

      // 修改鼠标样式为十字准星
      map.getCanvas().style.cursor = 'crosshair'

      // 添加地图点击事件
      map.once('click', handleMapClick)
    }

    // 修改地图点击处理函数
    const handleMapClick = (e) => {
      const { lng, lat } = e.lngLat
      
      // 添加临时标记
      if (tempMarker.value) {
        tempMarker.value.remove()
      }
      
      tempMarker.value = new mapboxgl.Marker({
        color: '#FFD700',
        draggable: true
      })
        .setLngLat([lng, lat])
        .addTo(map)

      // 更新表单数据
      insertForm.value.latitude = Number(lat.toFixed(8))
      insertForm.value.longitude = Number(lng.toFixed(8))

      // 询问用户是否确认插入
      ElMessageBox.confirm(
        `是否确认在此位置插入航点？\n纬度: ${lat.toFixed(8)}\n经度: ${lng.toFixed(8)}`,
        '确认插入',
        {
          confirmButtonText: '确认',
          cancelButtonText: '取消',
          type: 'info'
        }
      ).then(() => {
        confirmInsertPoint()
      }).catch(() => {
        // 用户取消，清理状态
        if (tempMarker.value) {
          tempMarker.value.remove()
          tempMarker.value = null
        }
        // 退出插入模式
        isInInsertMode.value = false
        // 恢复鼠标样式
        map.getCanvas().style.cursor = ''
        // 关闭提示
        ElMessage.closeAll()
      })
    }

    // 修改确认插入航点函数
    const confirmInsertPoint = () => {
      const { index, latitude, longitude, altitude, fileIndex, fileName, sourcePoint } = insertForm.value
      
      // 验证数据
      if (!isValidCoordinate(latitude, longitude)) {
        ElMessage.warning('请输入有效的经纬度坐标')
        return
      }
      
      // 创建新航点
      const newPoint = {
        ...sourcePoint,
        index: index + 1, // 新点的索引为当前点索引+1
        latitude,
        longitude,
        altitude,
        fileIndex,
        fileName,
        color: getFileColor(fileName)
      }

      // 更新同一文件中后续点的索引
      const updatedPoints = allWaypoints.value.map(point => {
        if (point.fileName === fileName && point.index > index) {
          return { ...point, index: point.index + 1 }
        }
        return point
      })

      // 添加新点并重新排序
      allWaypoints.value = [...updatedPoints, newPoint].sort((a, b) => {
        if (a.fileName !== b.fileName) {
          return a.fileName.localeCompare(b.fileName)
        }
        return a.index - b.index
      })

      // 更新地图点位数据
      const updatedFeatures = pointsData.value.features.map(feature => {
        if (feature.properties.fileName === fileName && 
            feature.properties.pointIndex > index) {
          const newIndex = feature.properties.pointIndex + 1
          return {
            ...feature,
            properties: {
              ...feature.properties,
              pointIndex: newIndex,
              id: `${feature.properties.fileIndex}-${newIndex}`,
              description: `${feature.properties.fileName}<br>航点 ${newIndex}`
            }
          }
        }
        return feature
      })

      // 创建新点位特征
      const newFeature = {
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [newPoint.longitude, newPoint.latitude]
        },
        properties: {
          id: `${fileIndex}-${newPoint.index}`,
          fileIndex: fileIndex,
          pointIndex: newPoint.index,
          fileName: fileName,
          color: newPoint.color,
          description: `${fileName}<br>航点 ${newPoint.index}`,
          inWorkArea: false,
          pointType: 'normal'
        }
      }

      // 更新地图点位集合并排序
      pointsData.value.features = [...updatedFeatures, newFeature].sort((a, b) => {
        if (a.properties.fileName !== b.properties.fileName) {
          return a.properties.fileName.localeCompare(b.properties.fileName)
        }
        return a.properties.pointIndex - b.properties.pointIndex
      })

      // 更新地图显示
      updatePointsLayer()
      updateLinesLayer()
      
      // 更新文件统计
      const file = fileList.value.find(f => f.name === fileName)
      if (file) {
        file.stats = getFileStats(fileName)
      }

      // 清理临时标记
      if (tempMarker.value) {
        tempMarker.value.remove()
        tempMarker.value = null
      }

      // 关闭对话框和提示
      insertDialogVisible.value = false
      ElMessage.closeAll()
      ElMessage.success('航点插入成功')

      // 触发表格刷新
      nextTick(() => {
        // 找到新插入的点并滚动到对应位置
        const tableRef = document.querySelector('.el-table__body-wrapper')
        if (tableRef) {
          const targetRow = Array.from(tableRef.querySelectorAll('.el-table__row'))
            .find(row => {
              const cells = row.querySelectorAll('td')
              return cells[0].textContent === String(newPoint.index) && 
                     cells[1].textContent === newPoint.fileName
            })
          
          if (targetRow) {
            targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' })
            // 高亮显示新插入的行
            tableRef.querySelectorAll('.el-table__row').forEach(row => {
              row.classList.remove('highlight-row')
            })
            targetRow.classList.add('highlight-row')
          }
        }
      })

      // 重置插入模式状态
      isInInsertMode.value = false
    }

    // 修改对话框关闭处理函数
    const handleInsertDialogClose = () => {
      // 清理临时标记
      if (tempMarker.value) {
        tempMarker.value.remove()
        tempMarker.value = null
      }
      
      // 重置状态
      isInInsertMode.value = false
      map.getCanvas().style.cursor = ''
      isSelectingPoint.value = false
      
      // 重置表单
      insertForm.value = {
        index: 1,
        inputMethod: 'map',
        latitude: null,
        longitude: null,
        altitude: 0,
        fileIndex: null,
        fileName: null,
        sourcePoint: null
      }
      currentInsertFile.value = null
      
      // 关闭所有提示
      ElMessage.closeAll()
    }

    // 修改表单中的选择方式切换处理
    const handleInputMethodChange = () => {
      if (insertForm.value.inputMethod === 'map') {
        enableMapSelection()
      } else {
        // 清理地图选点相关状态
        if (tempMarker.value) {
          tempMarker.value.remove()
          tempMarker.value = null
        }
        map.getCanvas().style.cursor = ''
        ElMessage.closeAll()
      }
    }

    // 更新地图点位
    const updateMapPoints = () => {
      // 清除现有点位
      pointsData.value.features = []
      
      // 重新添加所有点位
      allWaypoints.value.forEach((point, index) => {
        addPoints([point], point.fileIndex, point.fileName, point.color)
      })

      // 更新线条
      updateLinesLayer()
    }

    // 开始选点
    const startSelectPoint = () => {
      isSelectingPoint.value = true
      insertDialogVisible.value = false
      
      // 清除之前的临时标记
      if (tempMarker.value) {
        tempMarker.value.remove()
        tempMarker.value = null
      }

      // 修改鼠标样式
      map.getCanvas().style.cursor = 'crosshair'

      // 添加地图点击事件
      map.once('click', handleMapClick)
      
      // 添加提示信息
      ElMessage({
        message: '请在地图上点击选择位置',
        type: 'info',
        duration: 0,
        showClose: true
      })
    }

    // 完成选点
    const finishSelectPoint = () => {
      isSelectingPoint.value = false
      insertDialogVisible.value = true
    }

    // 更新标记位置
    const updateMarkerPosition = () => {
      if (tempMarker.value && isValidCoordinate(insertForm.value.latitude, insertForm.value.longitude)) {
        tempMarker.value.setLngLat([insertForm.value.longitude, insertForm.value.latitude])
      }
    }

    // 更新线条图层
    const updateLinesLayer = () => {
      // 移除现有图层
      ['route-lines', 'route-arrows'].forEach(layerId => {
        if (map.getLayer(layerId)) {
          map.removeLayer(layerId)
        }
      })
      if (map.getSource('route-lines')) {
        map.removeSource('route-lines')
      }

      // 创建线条特征
      const lineFeatures = []
      const arrowFeatures = []

      if (isMerged.value) {
        // 合并模式：按全局索引排序连线
        const sortedPoints = [...pointsData.value.features]
          .sort((a, b) => a.properties.pointIndex - b.properties.pointIndex)

        // 创建线条
        for (let i = 0; i < sortedPoints.length - 1; i++) {
          const start = sortedPoints[i]
          const end = sortedPoints[i + 1]

          lineFeatures.push({
            type: 'Feature',
            properties: {
              color: start.properties.color
            },
            geometry: {
              type: 'LineString',
              coordinates: [
                start.geometry.coordinates,
                end.geometry.coordinates
              ]
            }
          })

          // 创建箭头
          const arrowPosition = interpolatePoint(
            start.geometry.coordinates,
            end.geometry.coordinates,
            0.8
          )
          const bearing = getBearing(
            start.geometry.coordinates,
            end.geometry.coordinates
          )

          arrowFeatures.push({
            type: 'Feature',
            properties: {
              color: start.properties.color,
              bearing
            },
            geometry: {
              type: 'Point',
              coordinates: arrowPosition
            }
          })
        }
      } else {
        // 未合并模式：按文件分组连线
        const files = [...new Set(pointsData.value.features.map(f => f.properties.fileName))]

        files.forEach(fileName => {
          const filePoints = pointsData.value.features
            .filter(f => f.properties.fileName === fileName)
            .sort((a, b) => a.properties.pointIndex - b.properties.pointIndex)

          // 创建线条
          for (let i = 0; i < filePoints.length - 1; i++) {
            const start = filePoints[i]
            const end = filePoints[i + 1]

            lineFeatures.push({
              type: 'Feature',
              properties: {
                color: start.properties.color
              },
              geometry: {
                type: 'LineString',
                coordinates: [
                  start.geometry.coordinates,
                  end.geometry.coordinates
                ]
              }
            })

            // 创建箭头
            const arrowPosition = interpolatePoint(
              start.geometry.coordinates,
              end.geometry.coordinates,
              0.8
            )
            const bearing = getBearing(
              start.geometry.coordinates,
              end.geometry.coordinates
            )

            arrowFeatures.push({
              type: 'Feature',
              properties: {
                color: start.properties.color,
                bearing
              },
              geometry: {
                type: 'Point',
                coordinates: arrowPosition
              }
            })
          }
        })
      }

      // 添加线条数据源和图层
      map.addSource('route-lines', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: [...lineFeatures, ...arrowFeatures]
        }
      })

      // 添加线条图层
      map.addLayer({
        id: 'route-lines',
        type: 'line',
        source: 'route-lines',
        filter: ['==', '$type', 'LineString'],
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': ['get', 'color'],
          'line-width': 2,
          'line-opacity': 0.8
        }
      })

      // 添加箭头图层
      map.addLayer({
        id: 'route-arrows',
        type: 'symbol',
        source: 'route-lines',
        filter: ['==', '$type', 'Point'],
        layout: {
          'symbol-placement': 'point',
          'icon-image': 'arrow',
          'icon-size': 0.8,
          'icon-rotate': ['get', 'bearing'],
          'icon-allow-overlap': true,
          'icon-ignore-placement': true
        },
        paint: {
          'icon-color': ['get', 'color'],
          'icon-opacity': 0.8
        }
      })
    }

    // 添加计算两点之间插值点的函数
    const interpolatePoint = (start, end, fraction) => {
      const dx = end[0] - start[0]
      const dy = end[1] - start[1]
      return [
        start[0] + dx * fraction,
        start[1] + dy * fraction
      ]
    }

    // 添加计算方位角的函数
    const getBearing = (start, end) => {
      const dx = end[0] - start[0]
      const dy = end[1] - start[1]
      const bearing = (Math.atan2(dx, dy) * 180) / Math.PI
      return bearing
    }

    // 添加作业区相关函数
    const initDrawTools = () => {
      draw.value = new MapboxDraw({
        displayControlsDefault: false,
        controls: {
          polygon: true,
          trash: true
        }
      })
      
      map.addControl(draw.value)
      
      // 监听绘制完成事件
      map.on('draw.create', updateWorkAreas)
      map.on('draw.delete', updateWorkAreas)
      map.on('draw.update', updateWorkAreas)
    }

    // 添加更新作业区函数
    const updateWorkAreas = () => {
      // 获取所有作业区多边形
      const features = draw.value.getAll()
      workAreas.value = features.features

      // 按文件分组处理点位
      const fileGroups = {}
      pointsData.value.features.forEach(point => {
        const fileName = point.properties.fileName
        if (!fileGroups[fileName]) {
          fileGroups[fileName] = []
        }
        fileGroups[fileName].push(point)
      })

      // 处理每个文件的点位
      Object.values(fileGroups).forEach(filePoints => {
        // 按索引排序
        filePoints.sort((a, b) => a.properties.pointIndex - b.properties.pointIndex)
        
        // 判断每个点的状态
        filePoints.forEach((point, index) => {
          // 检查点是否在作业区内
          const isInWorkArea = workAreas.value.some(area => 
            isPointInPolygon([point.geometry.coordinates[0], point.geometry.coordinates[1]], area)
          )
          point.properties.inWorkArea = isInWorkArea

          // 获取前一个点和后一个点的状态
          const prevPoint = index > 0 ? filePoints[index - 1] : null
          const nextPoint = index < filePoints.length - 1 ? filePoints[index + 1] : null
          
          const prevInArea = prevPoint ? workAreas.value.some(area => 
            isPointInPolygon([prevPoint.geometry.coordinates[0], prevPoint.geometry.coordinates[1]], area)
          ) : false
          
          const nextInArea = nextPoint ? workAreas.value.some(area => 
            isPointInPolygon([nextPoint.geometry.coordinates[0], nextPoint.geometry.coordinates[1]], area)
          ) : isInWorkArea

          // 判断点的类型
          let pointType = POINT_TYPES.NORMAL
          if (!prevInArea && isInWorkArea) {
            // 前一个点在区域外，当前点在区域内，标记为驶入点
            pointType = POINT_TYPES.ENTRY
          } else if (isInWorkArea && !nextInArea) {
            // 当前点在区域内，下一个点在区域外，标记为驶出点
            pointType = POINT_TYPES.EXIT
          }

          // 更新点的属性
          point.properties.pointType = pointType

          // 更新对应的航点数据
          const waypoint = allWaypoints.value.find(w => 
            w.fileIndex === point.properties.fileIndex && 
            w.index === point.properties.pointIndex
          )
          if (waypoint) {
            waypoint.inWorkArea = isInWorkArea
            waypoint.pointType = pointType
          }
        })
      })

      // 更新地图显示
      updatePointsLayer()

      // 触发表格更新
      allWaypoints.value = [...allWaypoints.value]
    }

    // 修改判断点是否在多边形内的函数
    const isPointInPolygon = (point, polygon) => {
      const coordinates = polygon.geometry.coordinates[0]
      let inside = false
      
      for (let i = 0, j = coordinates.length - 1; i < coordinates.length; j = i++) {
        const xi = coordinates[i][0], yi = coordinates[i][1]
        const xj = coordinates[j][0], yj = coordinates[j][1]
        
        const intersect = ((yi > point[1]) !== (yj > point[1])) &&
          (point[0] < (xj - xi) * (point[1] - yi) / (yj - yi) + xi)
        
        if (intersect) inside = !inside
      }
      
      return inside
    }

    // 修改获取点类型文本的函数，更新驶出点的描述
    const getPointTypeText = (type) => {
      const types = {
        [POINT_TYPES.ENTRY]: '驶入点',
        [POINT_TYPES.EXIT]: '即将驶出',
        [POINT_TYPES.NORMAL]: '普通点'
      }
      return types[type] || '普通点'
    }

    // 修改地图初始化，添加箭头图标
    onMounted(() => {
      mapboxgl.accessToken = 'pk.eyJ1IjoieWlud2VpbmlkbmdsZSIsImEiOiJja3EzMHRzbGkwajdvMnBwaTc5d3B4NjNpIn0.VdMv_I1TppI_8sFOH5K9Hg'
      
      map = new mapboxgl.Map({
        container: mapContainer.value,
        style: 'mapbox://styles/mapbox/satellite-v9',
        center: [116.397428, 39.90923],
        zoom: 18,
        maxZoom: 22,
        minZoom: 3,
        renderWorldCopies: false
      })

      map.addControl(new mapboxgl.NavigationControl())
      
      // 初始化绘图工具
      initDrawTools()
      
      // 等待地图样式加载完成
      map.on('style.load', () => {
        // 首先添加箭头图标
        const img = new Image()
        img.src = arrowIcon
        img.onload = () => {
          map.addImage('arrow', img)
        updatePointsLayer()
          
          // 添加 WMS 图层
          map.addSource('wms-test-source', {
            'type': 'raster',
            'tiles': [
              'http://121.40.132.51:6080/arcgis/services/fengzhi/boyanhu/MapServer/WMSServer?' +
              'SERVICE=WMS' +
              '&VERSION=1.1.1' +
              '&REQUEST=GetMap' +
              '&FORMAT=image/png' +
              '&TRANSPARENT=true' +
              '&LAYERS=0' +
              '&exceptions=application/vnd.ogc.se_inimage' +
              '&SRS=EPSG:3857' +
              '&STYLES=' +
              '&WIDTH=256' +
              '&HEIGHT=256' +
              '&BBOX={bbox-epsg-3857}'
            ],
            'tileSize': 256
          })

          // 添加 WMS 图层到地图，放在点图层下面
          map.addLayer({
            'id': 'wms-test-layer',
            'type': 'raster',
            'source': 'wms-test-source',
            'paint': {
              'raster-opacity': 0.8
            },
            'layout': {
              'visibility': 'visible'
            }
          }, map.getLayer('points-circle') ? 'points-circle' : undefined)

          // 添加图层控制
          const layerControl = new mapboxgl.NavigationControl({
            showCompass: false
          })
          //map.addControl(layerControl, 'top-right')

          // 添加图层切换控件
          const layerSwitcher = document.createElement('div')
          layerSwitcher.className = 'mapboxgl-ctrl mapboxgl-ctrl-group layer-switcher'
          
          const toggleButton = document.createElement('button')
          toggleButton.className = 'mapboxgl-ctrl-icon layer-toggle'
          toggleButton.innerHTML = 'WMS'
          toggleButton.onclick = () => {
            const visibility = map.getLayoutProperty('wms-test-layer', 'visibility')
            if (visibility === 'visible') {
              map.setLayoutProperty('wms-test-layer', 'visibility', 'none')
              toggleButton.classList.remove('active')
            } else {
              map.setLayoutProperty('wms-test-layer', 'visibility', 'visible')
              toggleButton.classList.add('active')
            }
          }
          
          layerSwitcher.appendChild(toggleButton)
          document.querySelector('.mapboxgl-ctrl-top-right').appendChild(layerSwitcher)
        }
      })
    })

    // 修改合并函数，添加重新判断点类型的逻辑
    const handleMergePoints = () => {
      ElMessageBox.confirm(
        '合并后将重新编号所有航点，是否继续？',
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        // 按文件上传顺序和原始索引排序所有点
        const mergedPoints = allWaypoints.value
          .sort((a, b) => {
            if (a.fileIndex !== b.fileIndex) {
              return a.fileIndex - b.fileIndex
            }
            return a.index - b.index
          })
          .map((point, idx) => ({
            ...point,
            index: idx + 1  // 重新编号，从1开始
          }))

        // 更新所有航点数据
        allWaypoints.value = mergedPoints
        
        // 设置合并状态
        isMerged.value = true

        // 更新地图点位
        updateMapPoints()

        // 重新判断驶入点和驶出点
        updatePointsInWorkArea()

        // 更新文件统计信息
        fileList.value.forEach(file => {
          file.stats = getFileStats(file.name)
        })

        ElMessage.success('航点合并完成')
      }).catch(() => {
        // 用户取消操作
      })
    }

    // 添加切割相关函数
    const handleSplitPoints = () => {
      if (!isMerged.value) {
        ElMessage.warning('请先合并航点')
        return
      }

      ElMessageBox.prompt(
        '请输入每组航点的最大数量（不超过4000）',
        '切割航点',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputType: 'number',
          inputValue: splitForm.value.maxPoints,
          inputValidator: (value) => {
            const num = parseInt(value)
            return num > 0 && num <= 4000
          },
          inputErrorMessage: '请输入1-4000之间的数字'
        }
      ).then(({ value }) => {
        const maxPointsPerGroup = parseInt(value)
        splitPoints(maxPointsPerGroup)
      }).catch(() => {
        // 用户取消操作
      })
    }

    const splitPoints = (maxPointsPerGroup) => {
      // 获取所有点并按合并后的索引排序
      const sortedPoints = [...allWaypoints.value].sort((a, b) => a.index - b.index)
      
      // 查找作业区外的点
      const outsidePointIndices = []
      sortedPoints.forEach((point, index) => {
        const isOutside = !pointsData.value.features.find(
          f => f.properties.id === `${point.fileIndex}-${point.index}`
        )?.properties.inWorkArea
        
        if (isOutside) {
          outsidePointIndices.push(index)
        }
      })

      if (outsidePointIndices.length < 2) {
        ElMessage.error('找不到足够的作业区外的点来进行切割')
        return
      }

      // 创建分组
      const splitGroups = []
      let currentStartIndex = outsidePointIndices[0] // 从第一个作业区外的点开始
      
      // 遍历所有作业区外的点，寻找合适的切割点
      for (let i = 1; i < outsidePointIndices.length; i++) {
        const currentEndIndex = outsidePointIndices[i]
        const pointCount = currentEndIndex - currentStartIndex + 1
        
        // 如果当前段的点数超过最大值，需要在中间寻找作业区外的点进行切割
        if (pointCount > maxPointsPerGroup) {
          // 在当前段中寻找合适的作业区外的点作为切割点
          const possibleEndIndices = outsidePointIndices.filter(idx => 
            idx > currentStartIndex && 
            idx < currentEndIndex && 
            idx - currentStartIndex + 1 <= maxPointsPerGroup
          )
          
          if (possibleEndIndices.length > 0) {
            // 找到最后一个满足条件的点作为切割点
            const endIndex = possibleEndIndices[possibleEndIndices.length - 1]
            // 添加当前组
            splitGroups.push(sortedPoints.slice(currentStartIndex, endIndex + 1))
            // 更新起始点
            currentStartIndex = endIndex
            // 更新遍历索引
            i = outsidePointIndices.findIndex(idx => idx === endIndex)
          } else {
            // 如果找不到合适的切割点，发出警告并继续寻找下一个可能的切割点
            ElMessage.warning(`无法在点 ${currentStartIndex} 和点 ${currentEndIndex} 之间找到合适的切割点`)
            continue
          }
        } else if (i === outsidePointIndices.length - 1) {
          // 最后一段，直接添加
          splitGroups.push(sortedPoints.slice(currentStartIndex))
        } else if (pointCount >= maxPointsPerGroup * 0.75) {
          // 如果当前段点数达到最大值的75%，可以在这里切割
          splitGroups.push(sortedPoints.slice(currentStartIndex, currentEndIndex + 1))
          currentStartIndex = currentEndIndex
        }
      }

      // 验证所有分组
      const validGroups = splitGroups.filter(group => {
        // 验证组的大小
        if (group.length > maxPointsPerGroup) {
          return false
        }
        
        // 验证起点和终点是否在作业区外
        const startPoint = group[0]
        const endPoint = group[group.length - 1]
        const startOutside = !pointsData.value.features.find(
          f => f.properties.id === `${startPoint.fileIndex}-${startPoint.index}`
        )?.properties.inWorkArea
        const endOutside = !pointsData.value.features.find(
          f => f.properties.id === `${endPoint.fileIndex}-${endPoint.index}`
        )?.properties.inWorkArea
        
        return startOutside && endOutside
      })

      if (validGroups.length === 0) {
        ElMessage.error('无法找到合适的切割方案，请调整最大点数或确保有足够的非作业区点')
        return
      }

      // 重新编号并更新点位
      const newPoints = []
      validGroups.forEach((group, groupIndex) => {
        group.forEach((point, index) => {
          newPoints.push({
            ...point,
            index: index + 1,
            fileIndex: groupIndex,
            fileName: `航线${groupIndex + 1}`,
            color: markerColors[groupIndex % markerColors.length]
          })
        })
      })


      // 更新数据
      allWaypoints.value = newPoints
      
      // 更新文件列表
      fileList.value = validGroups.map((group, index) => ({
        name: `航线${index + 1}`,
        uploaded: true,
        stats: {
          waypointCount: group.length,
          validCount: group.length
        }
      }))

      // 清除原有的点位数据
      pointsData.value.features = []
      
      // 重新添加所有点位并更新地图
      newPoints.forEach(point => {
        const feature = {
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [point.longitude, point.latitude]
          },
          properties: {
            id: `${point.fileIndex}-${point.index}`,
            fileIndex: point.fileIndex,
            pointIndex: point.index,
            fileName: point.fileName,
            color: point.color,
            altitude: point.altitude,
            description: `${point.fileName}<br>航点 ${point.index}`,
            inWorkArea: false,
            pointType: POINT_TYPES.NORMAL
          }
        }
        pointsData.value.features.push(feature)
      })

      // 更新地图显示
      updatePointsLayer()
      updateLinesLayer()

      // 重置合并状态，因为切割后需要重新合并
      isMerged.value = false

      ElMessage.success(`切割完成，共分为${validGroups.length}组航线`)
    }

    // 修改导出相关函数
    const handleExport = () => {
      ElMessageBox.prompt(
        '请选择除草类型：1-行间除草，2-株间除草',
        '导出航点',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputType: 'select',
          inputValue: '1',
          inputPlaceholder: '请选择除草类型',
          inputValidator: (value) => ['1', '2'].includes(value),
          inputErrorMessage: '请选择有效的除草类型',
          inputOptions: [
            {
              label: '行间除草',
              value: '1'
            },
            {
              label: '株间除草',
              value: '2'
            }
          ]
        }
      ).then(({ value }) => {
        exportPoints(parseInt(value))
      }).catch(() => {
        // 用户取消操作
      })
    }

    const exportPoints = async (weedingType) => {
      try {
        // 按文件分组获取航点
        const groups = {}
        allWaypoints.value.forEach(point => {
          if (!groups[point.fileName]) {
            groups[point.fileName] = []
          }
          groups[point.fileName].push(point)
        })

        // 准备导出数据
        const exportData = {
          weedingType,
          groups: Object.entries(groups).map(([fileName, points]) => ({
            fileName,
            points: points.map(point => ({
              latitude: point.latitude,
              longitude: point.longitude,
              type: getPointExportType(point)
            }))
          }))
        }

        // 发送数据到后端
        //const response = await axios.post('http://localhost:5000/api/export', exportData)
        const response = await axios.post('http://121.40.132.51:5005/api/export', exportData)
        if (response.data.success) {
          // 处理每个文件的下载
          response.data.files.forEach(file => {
            // 创建Blob对象
            const blob = new Blob([file.content], { type: 'text/plain' })
            // 创建下载链接
            const downloadLink = document.createElement('a')
            downloadLink.href = URL.createObjectURL(blob)
            downloadLink.download = file.name
            // 触发下载
            document.body.appendChild(downloadLink)
            downloadLink.click()
            document.body.removeChild(downloadLink)
          })
          
          ElMessage.success('航点文件导出成功')
        } else {
          ElMessage.error(response.data.error || '导出失败')
        }
      } catch (error) {
        console.error('Export error:', error)
        ElMessage.error('导出失败：' + (error.response?.data?.error || error.message))
      }
    }

    // 获取点的导出类型
    const getPointExportType = (point) => {
      const feature = pointsData.value.features.find(
        f => f.properties.id === `${point.fileIndex}-${point.index}`
      )
      if (!feature) return 0 // 普通点

      switch (feature.properties.pointType) {
        case POINT_TYPES.ENTRY:
          return 1 // 驶入点
        case POINT_TYPES.EXIT:
          return 2 // 驶出点
        default:
          return 0 // 普通点
      }
    }

    // 添加异常点排查函数
    const handleCheckAbnormalPoints = () => {
      ElMessageBox.prompt(
        '请输入两点之间距离阈值（米）',
        '异常点排查',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputPattern: /^\d*\.?\d+$/,
          inputErrorMessage: '请输入有效的数字',
          inputValue: '0.4'
        }
      ).then(({ value }) => {
        const threshold = parseFloat(value)
        
        // 清除之前的异常点标记
        abnormalPoints.value.clear()
        
        // 按文件分组处理点位
        const fileGroups = {}
        pointsData.value.features.forEach(point => {
          const fileName = point.properties.fileName
          if (!fileGroups[fileName]) {
            fileGroups[fileName] = []
          }
          fileGroups[fileName].push(point)
        })

        // 检查每个文件中的点位
        Object.values(fileGroups).forEach(points => {
          // 按索引排序
          points.sort((a, b) => a.properties.pointIndex - b.properties.pointIndex)
          
          // 检查相邻点之间的距离
          for (let i = 0; i < points.length-1; i++) {
            const prevPoint = turf.point(points[i+1].geometry.coordinates)
            const currentPoint = turf.point(points[i].geometry.coordinates)
            
            // 计算距离（米）
            const distance = turf.distance(prevPoint, currentPoint, { units: 'meters' })
            
            if (distance < threshold) {
              // 将当前点标记为异常点
              abnormalPoints.value.add(points[i].properties.id)
            }
          }
        })

        // 更新点图层样式
        updatePointsLayer()

        // 显示结果提示
        const abnormalCount = abnormalPoints.value.size
        if (abnormalCount > 0) {
          ElMessage({
            message: `发现 ${abnormalCount} 个异常点`,
            type: 'warning',
            duration: 0,
            showClose: true
          })
        } else {
          ElMessage.success('未发现异常点')
        }
      })
    }

    // 添加偏移量相关状态和函数
    const offsetDialogVisible = ref(false)
    const offsetForm = ref({
      longitudeOffset: 0,
      latitudeOffset: 0
    })

    // 打开偏移量设置对话框
    const handleOffsetPoints = () => {
      offsetDialogVisible.value = true
    }

    // 关闭偏移量设置对话框
    const handleOffsetDialogClose = () => {
      offsetDialogVisible.value = false
      offsetForm.value = {
        longitudeOffset: 0,
        latitudeOffset: 0
      }
    }

    // 将厘米转换为经纬度增量
    const cmToCoordinate = (cm) => {
      // 地球半径（单位：米）
      const EARTH_RADIUS = 6378137
      // 将厘米转换为米
      const meters = cm / 100
      // 计算经纬度增量（弧度）
      const delta = meters / EARTH_RADIUS
      // 转换为度数
      return (delta * 180) / Math.PI
    }

    // 确认更新航点偏移量
    const confirmOffsetPoints = () => {
      const { longitudeOffset, latitudeOffset } = offsetForm.value
      
      // 计算经纬度增量
      const deltaLng = cmToCoordinate(longitudeOffset)
      const deltaLat = cmToCoordinate(latitudeOffset)
      
      // 更新所有航点的经纬度
      allWaypoints.value = allWaypoints.value.map(point => ({
        ...point,
        longitude: Number((point.longitude + deltaLng).toFixed(8)),
        latitude: Number((point.latitude + deltaLat).toFixed(8))
      }))
      
      // 更新地图点位
      pointsData.value.features = pointsData.value.features.map(feature => ({
        ...feature,
        geometry: {
          ...feature.geometry,
          coordinates: [
            Number((feature.geometry.coordinates[0] + deltaLng).toFixed(8)),
            Number((feature.geometry.coordinates[1] + deltaLat).toFixed(8))
          ]
        }
      }))
      
      // 更新地图显示
      updatePointsLayer()
      updateLinesLayer()
      
      // 关闭对话框并提示
      handleOffsetDialogClose()
      ElMessage.success('航点偏移量已更新')
    }

    // 添加框选删除相关函数
    const handleBoxSelect = () => {
      if (isBoxSelecting.value) {
        // 如果已经在框选模式，取消框选
        cancelBoxSelect()
      } else {
        // 启用框选模式
        startBoxSelect()
      }
    }

    const startBoxSelect = () => {
      isBoxSelecting.value = true
      selectedPoints.value.clear()
      
      // 启用多边形绘制
      draw.value.changeMode('draw_polygon')
      
      // 添加提示
      ElMessage({
        message: '请在地图上绘制多边形框选要删除的点',
        type: 'info',
        duration: 0,
        showClose: true
      })

      // 移除之前的事件监听器
      map.off('draw.create', handleBoxSelectComplete)
      // 重新添加事件监听器
      map.on('draw.create', handleBoxSelectComplete)
    }

    const handleBoxSelectComplete = (e) => {
      const polygon = e.features[0]
      
      // 清空之前的选择
      selectedPoints.value.clear()
      
      // 检查每个点是否在多边形内
      pointsData.value.features.forEach(point => {
        if (turf.booleanPointInPolygon(
          turf.point(point.geometry.coordinates),
          polygon
        )) {
          selectedPoints.value.add(point.properties.id)
        }
      })

      // 更新点图层样式以显示选中的点
      updatePointsLayer()

      // 显示确认对话框
      ElMessageBox.confirm(
        `确定要删除选中的 ${selectedPoints.value.size} 个点吗？`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        // 删除选中的点
        deleteSelectedPoints()
      }).catch(() => {
        // 取消删除
        cancelBoxSelect()
      }).finally(() => {
        // 删除当前绘制的多边形
        draw.value.delete(polygon.id)
        // 重置绘图模式
        draw.value.changeMode('simple_select')
      })
    }

    const deleteSelectedPoints = () => {
      if (selectedPoints.value.size === 0) {
        ElMessage.warning('没有选中任何点')
        return
      }

      // 删除选中的点
      allWaypoints.value = allWaypoints.value.filter(point => 
        !selectedPoints.value.has(`${point.fileIndex}-${point.index}`)
      )

      // 更新地图点位
      pointsData.value.features = pointsData.value.features.filter(feature =>
        !selectedPoints.value.has(feature.properties.id)
      )

      // 重新编号每个文件中的点
      const fileGroups = {}
      allWaypoints.value.forEach(point => {
        if (!fileGroups[point.fileName]) {
          fileGroups[point.fileName] = []
        }
        fileGroups[point.fileName].push(point)
      })

      Object.values(fileGroups).forEach(points => {
        points.sort((a, b) => a.index - b.index)
        points.forEach((point, index) => {
          point.index = index + 1
        })
      })

      // 更新点位ID和描述
      pointsData.value.features.forEach(feature => {
        const point = allWaypoints.value.find(p => 
          p.fileIndex === feature.properties.fileIndex && 
          p.fileName === feature.properties.fileName
        )
        if (point) {
          feature.properties.pointIndex = point.index
          feature.properties.id = `${point.fileIndex}-${point.index}`
          feature.properties.description = `${point.fileName}<br>航点 ${point.index}`
        }
      })

      // 更新地图显示
      updatePointsLayer()
      updateLinesLayer()

      // 更新文件统计
      fileList.value.forEach(file => {
        file.stats = getFileStats(file.name)
      })

      // 清理框选状态
      cancelBoxSelect()
      
      ElMessage.success(`已删除 ${selectedPoints.value.size} 个点`)
    }

    const cancelBoxSelect = () => {
      isBoxSelecting.value = false
      selectedPoints.value.clear()
      
      // 删除所有绘制的多边形
      const features = draw.value.getAll()
      features.features.forEach(feature => {
        draw.value.delete(feature.id)
      })

      // 重置绘图模式
      draw.value.changeMode('simple_select')
      
      // 更新点图层样式
      updatePointsLayer()
      
      // 关闭提示
      ElMessage.closeAll()

      // 移除事件监听器
      map.off('draw.create', handleBoxSelectComplete)
    }

    // 添加删除异常点函数
    const handleDeleteAbnormalPoints = () => {
      if (abnormalPoints.value.size === 0) {
        ElMessage.warning('没有异常点需要删除')
        return
      }

      ElMessageBox.confirm(
        `确定要删除 ${abnormalPoints.value.size} 个异常点吗？`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        // 删除异常点
        selectedPoints.value = new Set(abnormalPoints.value)
        deleteSelectedPoints()
        // 清除异常点标记
        abnormalPoints.value.clear()
        // 更新地图显示
        updatePointsLayer()
        ElMessage.success('异常点已删除')
      }).catch(() => {
        // 用户取消删除操作
      })
    }

    return {
      mapContainer,
      fileList,
      allWaypoints,
      activeTab,
      handleFileChange,
      handleDeleteFile,
      uploadFile,
      getModeText,
      getFunctionText,
      sidebarWidth,
      mapHeight,
      tableHeight,
      handleResizeStart,
      handleRowClick,
      waypoints,
      getRowStyle,
      handleFileClick,
      activeFile,
      getFileColor,
      getFileStats,
      loading,
      pointsData,
      handleDeletePoint,
      insertDialogVisible,
      insertForm,
      maxInsertIndex,
      canInsert,
      handleInsertPoint,
      confirmInsertPoint,
      handleInsertDialogClose,
      isSelectingPoint,
      startSelectPoint,
      finishSelectPoint,
      updateMarkerPosition,
      getPointTypeText,
      handleMergePoints,
      isMerged,
      handleSplitPoints,
      splitForm,
      handleExport,
      handleCheckAbnormalPoints,
      abnormalPoints,
      handleBoxSelect,
      isBoxSelecting,
      selectedPoints,
      offsetDialogVisible,
      offsetForm,
      handleOffsetPoints,
      handleOffsetDialogClose,
      confirmOffsetPoints,
      handleDeleteAbnormalPoints
    }
  }
}
</script>

<style scoped>
.container {
  display: flex;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background-color: #f5f7fa;
}

.sidebar {
  padding: 16px;
  background-color: white;
  border-right: 1px solid #e6e6e6;
  position: relative;
  min-width: 280px;
  max-width: 30%;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.resize-handle {
  position: absolute;
  z-index: 100;
}

.resize-handle.vertical {
  right: -3px;
  width: 6px;
}

.resize-handle.horizontal {
  bottom: -3px;
  height: 6px;
}

.main-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
  gap: 16px; /* 添加间距 */
}

#map {
  position: relative;
  min-height: 40%;
  max-height: 80%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.data-table {
  background-color: white;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.file-list {
  margin-top: 24px;
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
  height: calc(100% - 120px);
  display: flex;
  flex-direction: column;
}

.file-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  margin: 4px 0;
  border-radius: 4px;
  transition: all 0.3s;
}

.file-content {
  flex: 1;
  cursor: pointer;
}

.file-actions {
  opacity: 0;
  transition: opacity 0.3s;
}

.file-item:hover {
  background-color: #f5f7fa;
}

.file-item:hover .file-actions {
  opacity: 1;
}

.file-item.active {
  background-color: #ecf5ff;
}

.file-item.active .file-actions {
  opacity: 1;
}

.file-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  margin-left: 8px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding-top: 8px;
  border-top: 1px dashed #ebeef5;
  margin-top: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.stat-value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

/* 修改滚动条样式 */
:deep(.el-scrollbar__wrap) {
  padding-right: 8px;
}

:deep(.el-scrollbar__bar.is-vertical) {
  width: 6px;
}

:deep(.el-scrollbar__thumb) {
  background-color: #c0c4cc;
  border-radius: 3px;
}

.upload-demo {
  margin-bottom: 24px;
}

/* 美化滚动条 */
:deep(.el-table__body-wrapper::-webkit-scrollbar) {
  width: 8px;
  height: 8px;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar-thumb) {
  background: #c0c4cc;
  border-radius: 4px;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar-track) {
  background: #f5f7fa;
  border-radius: 4px;
}

/* 表格样式优化 */
:deep(.el-table) {
  border-radius: 4px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
  font-weight: 500;
  color: #303133;
}

:deep(.el-table__row) {
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
}

:deep(.el-table__row:hover) {
  background-color: #f0f2f5;
}

/* 标签页样式优化 */
:deep(.el-tabs__nav-wrap) {
  padding: 0 8px;
}

:deep(.el-tabs__item) {
  font-size: 14px;
  padding: 0 16px;
}

/* 按钮样式优化 */
:deep(.el-button) {
  padding: 8px 16px;
  font-weight: 500;
}

/* 上传区域样式 */
:deep(.el-upload-list) {
  max-height: 180px;
  overflow-y: auto;
  border-radius: 4px;
  border: 1px solid #ebeef5;
  padding: 4px 8px;
}

/* 文件列表项样式 */
:deep(.el-list-item) {
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

:deep(.el-list-item:hover) {
  background-color: #f5f7fa;
}

/* 图标样式 */
:deep(.el-icon) {
  margin-right: 8px;
  color: #909399;
}

.table-container {
  height: 100%;
  overflow: hidden;
}

/* 确保表格内容可以滚动 */
:deep(.el-table__body-wrapper) {
  overflow-y: auto;
}

:deep(.el-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs__content) {
  flex: 1;
  padding: 10px 0;
}

:deep(.el-tab-pane) {
  height: 100%;
}

/* 优化表格头部固定时的样式 */
:deep(.el-table__header-wrapper) {
  background-color: #fff;
}

:deep(.el-table__fixed-header-wrapper) {
  background-color: #fff;
}

/* 确保表格在固定高度内可滚动 */
:deep(.el-table) {
  height: 100%;
}

:deep(.el-table__body-wrapper) {
  overflow-y: auto;
}

/* 表格行样式 */
:deep(.el-table__row) {
  cursor: pointer;
  transition: background-color 0.2s;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

/* 表格头部样式 */
:deep(.el-table th) {
  background-color: #f5f7fa;
  font-weight: 500;
  color: #303133;
}

.file-item {
  cursor: pointer;
  padding: 8px 16px;
  margin: 4px 0;
  border-radius: 4px;
  transition: all 0.3s;
}

.file-item:hover {
  background-color: #f5f7fa;
}

.file-item.active {
  background-color: #ecf5ff;
  color: #409eff;
}

.file-item.active :deep(.el-icon) {
  color: #409eff;
}

/* 调整表格文件名列样式 */
:deep(.el-table .cell) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 表格行高亮样式 */
.highlight-row {
  background-color: #ecf5ff !important;
}

/* 表格行高亮动画 */
.el-table__row {
  transition: background-color 0.3s ease;
}

/* 删除按钮样式 */
.el-button--danger.el-button--link {
  padding: 2px 4px;
}

.el-button--danger.el-button--link:hover {
  background-color: rgba(245, 108, 108, 0.1);
  border-radius: 4px;
}

.insert-point-form {
  padding: 20px;
}

.map-select-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.map-tip {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.selected-point-info {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.coords-display {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.coord-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.coord-label {
  min-width: 50px;
  color: #606266;
  font-size: 14px;
}

:deep(.el-input) {
  width: 180px;
}

:deep(.el-input-number) {
  width: 180px;
}

/* 选点时的鼠标样式 */
.selecting {
  cursor: crosshair;
}

.dialog-footer {
  padding: 20px 0 0;
}

/* 添加作业区相关样式 */
.mapboxgl-ctrl-group {
  margin-right: 10px;
}

/* 自定义绘图控件样式 */
.mapbox-gl-draw_ctrl-draw-btn {
  border-radius: 4px !important;
  margin: 2px !important;
}

.mapbox-gl-draw_polygon {
  background-image: url('data:image/svg+xml;utf8,<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M3 3h18v18H3z" fill="none"/><path d="M15 5h5v5h-5z M4 14h5v5H4z M15 14h5v5h-5z M4 4h5v5H4z" fill="%23666"/></svg>') !important;
}

/* 添加按钮间距 */
.ml-3 {
  margin-left: 0 !important;
}

/* 在 style 部分添加图层切换按钮样式 */
.layer-switcher {
  margin-top: 10px;
}

.layer-toggle {
  padding: 5px 10px;
  background: white;
  border: none;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  color: #666;
}

.layer-toggle.active {
  background: #4264fb;
  color: white;
}

.layer-toggle:hover {
  background: #f0f0f0;
}

.layer-toggle.active:hover {
  background: #315def;
}

/* 添加新的样式 */
.button-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
}

.action-button {
  width: 100%;
  margin: 0 !important;
}

.upload-demo {
  width: 100%;
}

.upload-demo :deep(.el-upload) {
  width: 100%;
}

.upload-demo :deep(.el-upload-list) {
  width: 100%;
}

/* 添加表格行高亮样式 */
:deep(.el-table__row.highlight-row) {
  background-color: #ecf5ff !important;
  transition: background-color 0.3s;
}

:deep(.el-table__row:hover) {
  cursor: pointer;
}

/* 优化表格内容显示 */
:deep(.el-table__cell) {
  padding: 8px 0;
}

:deep(.el-table--enable-row-hover .el-table__body tr:hover > td) {
  background-color: #f5f7fa;
}
</style>