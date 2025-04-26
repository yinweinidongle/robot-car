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

          <!-- 添加偏移量记录查看按钮 -->
          <el-button type="primary" @click="showOffsetHistoryDialog" class="action-button">
            偏移量设置记录
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
        
        <!-- 地图右侧控制按钮 -->
        <div class="map-controls">
          <el-button 
            type="primary" 
            class="control-button wms-button" 
            @click="showWmsLayersMenu = !showWmsLayersMenu">
            WMS
          </el-button>
          
          <!-- 添加测距按钮 -->
          <el-button
            type="primary"
            class="control-button measure-button"
            @click="handleMeasureDistance">
            {{ isMeasuringDistance ? '取消测距' : '测距工具' }}
          </el-button>
          
          <!-- 添加ZAW障碍物按钮 -->
          <el-button
            type="primary"
            class="control-button zaw-button"
            @click="handleObstacleDrawing">
            障碍物
          </el-button>
          
          <!-- 添加障碍物列表按钮 -->
          <el-button
            type="primary"
            class="control-button obstacles-list-button"
            @click="showObstacleListDialog">
            障碍物列表
          </el-button>
          
          <!-- 添加excel表格管理按钮 -->
          <el-button
            type="primary"
            class="control-button excel-button"
            @click="showTableManagementDialog">
            表格管理
          </el-button>
          
          <!-- 添加标记组按钮 -->
          <el-button
            type="primary" 
            class="control-button marker-group-button"
            @click="showMarkerGroupDialog">
            标记组
          </el-button>
          
          <!-- 添加标记按钮 -->
          <el-button
            type="primary"
            class="control-button add-marker-button"
            @click="handleAddMarker">
            添加标记
          </el-button>
        </div>
        
        <!-- WMS图层菜单 -->
        <div class="wms-layers-menu" v-if="showWmsLayersMenu">
          <div class="wms-layers-header">
            <h3>WMS图层列表</h3>
            <el-button type="text" @click="showWmsLayersMenu = false">关闭</el-button>
          </div>
          <el-divider></el-divider>
          <div class="wms-layers-list">
            <div v-for="layer in wmsLayers" :key="layer.id" class="wms-layer-item">
              <el-checkbox 
                v-model="layer.enabled" 
                @change="(val) => toggleWmsLayer(layer.id, val)">
                {{ layer.name }}
              </el-checkbox>
            </div>
          </div>
          <el-divider></el-divider>
          <div class="wms-layers-footer">
            <el-button type="primary" size="small" @click="handleOpenWmsLayerManager">
              图层管理
            </el-button>
          </div>
        </div>
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
      width="1100px"
      :close-on-click-modal="false"
      @close="handleOffsetDialogClose">
      <div class="offset-form">
        <el-table :data="vehicleSettings" border style="width: 100%">
          <el-table-column prop="vehicle_name" label="车辆名称" width="120" />
          <el-table-column prop="longitude_offset" label="经度偏移 (°)" width="150">
            <template #default="scope">
              {{ scope.row.longitude_offset }}
            </template>
          </el-table-column>
          <el-table-column prop="latitude_offset" label="纬度偏移 (°)" width="150">
            <template #default="scope">
              {{ scope.row.latitude_offset }}
            </template>
          </el-table-column>
          <el-table-column prop="line_width" label="线条宽度" width="100" />
          <el-table-column prop="line_color" label="线条颜色" width="100">
            <template #default="scope">
              <div class="color-preview" :style="{ backgroundColor: scope.row.line_color }"></div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="280">
            <template #default="scope">
              <el-button
                type="primary"
                link
                @click="handleEditVehicle(scope.row)">
                编辑
              </el-button>
              <el-button
                type="success"
                link
                @click="handleConfirmOffset(scope.row)">
                确认
              </el-button>
              <el-button
                type="danger"
                link
                @click="handleDeleteVehicle(scope.row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="add-vehicle-form" v-if="isAddingVehicle">
          <h3>添加新车辆</h3>
          <el-form :model="editVehicleForm" label-width="100px">
            <el-form-item label="车辆名称">
              <el-input v-model="editVehicleForm.vehicle_name" />
            </el-form-item>
            <el-form-item label="经度偏移">
              <el-input-number 
                v-model="editVehicleForm.longitude_offset" 
                controls-position="right" />
            </el-form-item>
            <el-form-item label="纬度偏移">
              <el-input-number 
                v-model="editVehicleForm.latitude_offset" 
                controls-position="right" />
            </el-form-item>
            <el-form-item label="线条宽度">
              <el-input-number 
                v-model="editVehicleForm.line_width" 
                :precision="1"
                :step="0.5"
                :min="0.5"
                controls-position="right" />
            </el-form-item>
            <el-form-item label="线条颜色">
              <el-color-picker v-model="editVehicleForm.line_color" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveVehicle">保存</el-button>
              <el-button @click="cancelAddVehicle">取消</el-button>
            </el-form-item>
          </el-form>
        </div>
        <div v-else class="add-vehicle-btn">
          <el-button type="primary" @click="startAddVehicle">添加车辆</el-button>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleOffsetDialogClose">关闭</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 编辑车辆对话框 -->
    <el-dialog
      v-model="editVehicleDialogVisible"
      title="编辑车辆设置"
      width="500px"
      :close-on-click-modal="false">
      <el-form :model="editVehicleForm" label-width="100px">
        <el-form-item label="车辆名称">
          <el-input v-model="editVehicleForm.vehicle_name" />
        </el-form-item>
        <el-form-item label="经度偏移">
          <el-input-number 
            v-model="editVehicleForm.longitude_offset" 
            controls-position="right" />
        </el-form-item>
        <el-form-item label="纬度偏移">
          <el-input-number 
            v-model="editVehicleForm.latitude_offset" 
            controls-position="right" />
        </el-form-item>
        <el-form-item label="线条宽度">
          <el-input-number 
            v-model="editVehicleForm.line_width" 
            :precision="1"
            :step="0.5"
            :min="0.5"
            controls-position="right" />
        </el-form-item>
        <el-form-item label="线条颜色">
          <el-color-picker v-model="editVehicleForm.line_color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editVehicleDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="updateVehicle">确认</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- WMS图层管理对话框 -->
    <el-dialog
      v-model="wmsManagerDialogVisible"
      title="WMS图层管理"
      width="800px"
      :close-on-click-modal="false">
      <div class="wms-manager">
        <el-table :data="wmsLayers" border style="width: 100%">
          <el-table-column prop="name" label="图层名称" width="150" />
          <el-table-column prop="url" label="图层地址" min-width="250">
            <template #default="scope">
              <el-tooltip :content="scope.row.url" placement="top" :show-after="500">
                <div class="ellipsis-text">{{ scope.row.url }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="layer_id" label="图层编号" width="100" />
          <el-table-column prop="opacity" label="透明度" width="100">
            <template #default="scope">
              {{ (scope.row.opacity * 100).toFixed(0) }}%
            </template>
          </el-table-column>
          <el-table-column prop="enabled" label="状态" width="80">
            <template #default="scope">
              <el-tag :type="scope.row.enabled ? 'success' : 'info'">
                {{ scope.row.enabled ? '已启用' : '已禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="scope">
              <el-button
                type="primary"
                link
                @click="handleEditWmsLayer(scope.row)">
                编辑
              </el-button>
              <el-button
                type="danger"
                link
                @click="handleDeleteWmsLayer(scope.row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="add-wms-layer" v-if="isAddingWmsLayer">
          <h3>添加新WMS图层</h3>
          <el-form :model="editWmsLayerForm" label-width="100px">
            <el-form-item label="图层名称" required>
              <el-input v-model="editWmsLayerForm.name" />
            </el-form-item>
            <el-form-item label="图层地址" required>
              <el-input v-model="editWmsLayerForm.url" />
            </el-form-item>
            <el-form-item label="图层编号" required>
              <el-input v-model="editWmsLayerForm.layer_id" />
            </el-form-item>
            <el-form-item label="透明度">
              <el-slider
                v-model="editWmsLayerForm.opacity"
                :min="0"
                :max="1"
                :step="0.1"
                :format-tooltip="value => `${(value * 100).toFixed(0)}%`" />
            </el-form-item>
            <el-form-item label="状态">
              <el-switch
                v-model="editWmsLayerForm.enabled"
                :active-text="'启用'"
                :inactive-text="'禁用'" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveWmsLayer">保存</el-button>
              <el-button @click="cancelAddWmsLayer">取消</el-button>
            </el-form-item>
          </el-form>
        </div>
        <div v-else class="add-wms-layer-btn">
          <el-button type="primary" @click="startAddWmsLayer">添加WMS图层</el-button>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="wmsManagerDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 编辑WMS图层对话框 -->
    <el-dialog
      v-model="editWmsLayerDialogVisible"
      title="编辑WMS图层"
      width="500px"
      :close-on-click-modal="false">
      <el-form :model="editWmsLayerForm" label-width="100px">
        <el-form-item label="图层名称" required>
          <el-input v-model="editWmsLayerForm.name" />
        </el-form-item>
        <el-form-item label="图层地址" required>
          <el-input v-model="editWmsLayerForm.url" />
        </el-form-item>
        <el-form-item label="图层编号" required>
          <el-input v-model="editWmsLayerForm.layer_id" />
        </el-form-item>
        <el-form-item label="透明度">
          <el-slider
            v-model="editWmsLayerForm.opacity"
            :min="0"
            :max="1"
            :step="0.1"
            :format-tooltip="value => `${(value * 100).toFixed(0)}%`" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch
            v-model="editWmsLayerForm.enabled"
            :active-text="'启用'"
            :inactive-text="'禁用'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editWmsLayerDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="updateWmsLayer">确认</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 偏移量历史记录对话框 -->
    <el-dialog
      v-model="offsetHistoryDialogVisible"
      title="偏移量设置历史记录"
      width="800px"
    >
      <el-table :data="offsetHistoryRecords" stripe style="width: 100%" v-loading="historyLoading">
        <el-table-column prop="vehicle_name" label="车辆名称" width="100" />
        <el-table-column prop="longitude_offset" label="经度偏移" width="120">
          <template #default="scope">
            {{ scope.row.longitude_offset }}
          </template>
        </el-table-column>
        <el-table-column prop="latitude_offset" label="纬度偏移" width="120">
          <template #default="scope">
            {{ scope.row.latitude_offset }}
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" label="设置时间" width="180">
          <template #default="scope">
            {{ formatTimestamp(scope.row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="notes" label="备注" />
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="historyTotalCount"
          :page-size="historyPageSize"
          :current-page="historyCurrentPage"
          @current-change="handleHistoryPageChange"
        />
      </div>
    </el-dialog>
    
    <!-- 添加障碍物信息对话框 -->
    <el-dialog
      v-model="obstacleDialogVisible"
      :title="editingObstacle ? '编辑障碍物' : '添加障碍物'"
      width="500px"
      :close-on-click-modal="false"
      @close="handleObstacleDialogClose">
      <div class="obstacle-form">
        <el-form :model="obstacleForm" label-width="120px">
          <el-form-item label="障碍物名称" required>
            <el-input v-model="obstacleForm.name" placeholder="请输入障碍物名称" />
          </el-form-item>
          <el-form-item label="障碍物尺寸" required>
            <el-input v-model="obstacleForm.area" type="number" placeholder="面积(㎡)">
              <template #append>㎡</template>
            </el-input>
          </el-form-item>
          <el-form-item label="障碍物高度" required>
            <el-input-number 
              v-model="obstacleForm.height" 
              :precision="2" 
              :step="0.01" 
              :min="0" 
              controls-position="right"
              style="width: 100%"
              placeholder="高度(m)" />
          </el-form-item>
          <el-form-item label="障碍物颜色">
            <div class="color-picker-container">
              <el-color-picker v-model="obstacleForm.color" />
              <div class="color-preview-large" :style="{ backgroundColor: obstacleForm.color }"></div>
            </div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleObstacleDialogClose">取消</el-button>
          <el-button type="primary" @click="saveObstacle">确认</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 添加障碍物列表对话框 -->
    <el-dialog
      v-model="obstacleListDialogVisible"
      title="障碍物列表"
      width="800px"
      :close-on-click-modal="false">
      <div class="obstacle-list">
        <el-table :data="obstacles" border style="width: 100%" v-loading="loading">
          <el-table-column prop="name" label="障碍物名称" width="150" />
          <el-table-column prop="area" label="尺寸(㎡)" width="100">
            <template #default="scope">
              {{ scope.row.area.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="height" label="高度(m)" width="100" />
          <el-table-column prop="color" label="颜色" width="120">
            <template #default="scope">
              <div class="color-preview-row">
                <div class="color-preview" :style="{ backgroundColor: scope.row.color }"></div>
                <span class="color-value">{{ scope.row.color }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="180">
            <template #default="scope">
              <el-button
                type="primary"
                link
                @click="locateObstacle(scope.row)">
                <el-icon><Location /></el-icon> 定位
              </el-button>
              <el-button
                type="danger"
                link
                @click="deleteObstacle(scope.row)">
                <el-icon><Delete /></el-icon> 删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 添加航点偏移量设置提示对话框 -->
    <el-dialog
      v-model="offsetPromptDialogVisible"
      title="设置航点偏移量"
      width="400px"
      :close-on-click-modal="false">
      <div class="offset-prompt">
        <p>是否需要为上传的航点文件设置偏移量？</p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleOffsetPromptNo">否</el-button>
          <el-button type="primary" @click="handleOffsetPromptYes">
            是
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加航点上传偏移量设置对话框 -->
    <el-dialog
      v-model="uploadOffsetDialogVisible"
      title="设置航点偏移量"
      width="650px"
      :close-on-click-modal="false"
      @close="handleUploadOffsetDialogClose">
      <div class="upload-offset-form">
        <p class="upload-offset-desc">请为当前上传的航点文件设置偏移量：</p>
        
        <!-- <div v-if="uploaderOffsetData.length > 0" class="offset-preview">
          <div class="preview-title">偏移量预览：</div>
          <div class="preview-content">
            <div class="preview-point original"></div>
            <div class="preview-arrow">→</div>
            <div 
              class="preview-point offset" 
              :style="{
                left: `${50 + (uploaderOffsetData[0].longitude_offset * 10000)}px`,
                top: `${50 + (uploaderOffsetData[0].latitude_offset * -10000)}px`
              }">
            </div>
          </div>
          <div class="preview-info">
            经度偏移：{{ uploaderOffsetData[0].longitude_offset }}° / 
            纬度偏移：{{ uploaderOffsetData[0].latitude_offset }}°
          </div>
        </div> -->

        <el-table :data="uploaderOffsetData" border style="width: 100%">
          <el-table-column prop="vehicle_name" label="车辆名称" />
          <el-table-column label="经度偏移 (°)" width="150">
            <template #default="scope">
              <el-input-number 
                v-model="scope.row.longitude_offset" 
                controls-position="right"
                :precision="8"
                :step="0.0000001" />
            </template>
          </el-table-column>
          <el-table-column label="纬度偏移 (°)" width="150">
            <template #default="scope">
              <el-input-number 
                v-model="scope.row.latitude_offset" 
                controls-position="right"
                :precision="8"
                :step="0.0000001" />
            </template>
          </el-table-column>
          <el-table-column label="线条宽度" width="90">
            <template #default="scope">
              {{ scope.row.line_width || 2 }}
            </template>
          </el-table-column>
          <el-table-column label="线条颜色" width="80">
            <template #default="scope">
              <div class="color-preview" :style="{ backgroundColor: scope.row.line_color || scope.row.color || '#0000FF' }"></div>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="scope">
              <el-button
                type="primary"
                link
                class="confirm-btn"
                @click="applySpecificOffset(scope.row)">
                应用此偏移
              </el-button>
              <el-button
                type="danger"
                link
                @click="removeOffsetRow(scope.$index)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <!-- <div class="add-btn" style="margin-top: 10px;">
          <el-button type="primary" @click="addOffsetRow">添加车辆</el-button>
        </div> -->
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleUploadOffsetDialogClose">取消</el-button>
          <!-- <el-button type="primary" @click="confirmUploadOffset">确认并上传</el-button> -->
        </span>
      </template>
    </el-dialog>

    <!-- 导出偏移量设置对话框 -->
    <el-dialog
      v-model="exportOffsetDialogVisible"
      title="设置航点偏移量"
      width="650px"
      :close-on-click-modal="false"
      @close="handleExportOffsetDialogClose">
      <div class="upload-offset-form">
        <p class="upload-offset-desc">请为当前导出的航点文件设置偏移量：</p>
        
        <!-- <div v-if="exportOffsetData.length > 0" class="offset-preview">
          <div class="preview-title">偏移量预览：</div>
          <div class="preview-content">
            <div class="preview-point original"></div>
            <div class="preview-arrow">→</div>
            <div 
              class="preview-point offset" 
              :style="{
                left: `${50 + (exportOffsetData[0].longitude_offset * 10000)}px`,
                top: `${50 + (exportOffsetData[0].latitude_offset * -10000)}px`
              }">
            </div>
          </div>
          <div class="preview-info">
            经度偏移：{{ exportOffsetData[0].longitude_offset }}° / 
            纬度偏移：{{ exportOffsetData[0].latitude_offset }}°
          </div>
        </div> -->

        <el-table :data="exportOffsetData" border style="width: 100%">
          <el-table-column prop="vehicle_name" label="车辆名称" />
          <el-table-column label="经度偏移 (°)" width="150">
            <template #default="scope">
              <el-input-number 
                v-model="scope.row.longitude_offset" 
                controls-position="right"
                :precision="8"
                :step="0.0000001" />
            </template>
          </el-table-column>
          <el-table-column label="纬度偏移 (°)" width="150">
            <template #default="scope">
              <el-input-number 
                v-model="scope.row.latitude_offset" 
                controls-position="right"
                :precision="8"
                :step="0.0000001" />
            </template>
          </el-table-column>
          <el-table-column label="线条宽度" width="90">
            <template #default="scope">
              {{ scope.row.line_width || 2 }}
            </template>
          </el-table-column>
          <el-table-column label="线条颜色" width="80">
            <template #default="scope">
              <div class="color-preview" :style="{ backgroundColor: scope.row.line_color || scope.row.color || '#0000FF' }"></div>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="scope">
              <el-button
                type="primary"
                link
                class="confirm-btn"
                @click="applyExportOffset(scope.row)">
                应用此偏移
              </el-button>
              <el-button
                type="danger"
                link
                @click="removeExportOffsetRow(scope.$index)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <!-- <div class="add-btn" style="margin-top: 10px;">
          <el-button type="primary" @click="addExportOffsetRow">添加车辆</el-button>
        </div> -->
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleExportOffsetDialogClose">取消</el-button>
          <!-- <el-button type="primary" @click="confirmExportOffset">确认并导出</el-button> -->
        </span>
      </template>
    </el-dialog>

    <!-- Excel表格管理对话框 -->
    <el-dialog
      v-model="tableManagementDialogVisible"
      title="协和成地块作业地块"
      width="80%"
      :close-on-click-modal="false">
      <div class="table-management-container">
        <div class="table-management-toolbar">
          <el-button type="primary" @click="handleAddTableRecord">新增记录</el-button>
          <el-button type="success" @click="exportToExcel">导出Excel</el-button>
        </div>
        <el-table :data="tableRecords" border style="width: 100%">
          <el-table-column prop="id" label="作业行号" width="80" />
          <el-table-column prop="cCarNo" label="C车编号" />
          <el-table-column prop="cLastTime" label="C系列最后一次采样时间" />
          <el-table-column prop="hCarNo" label="H车编号" />
          <el-table-column prop="hLastTime" label="H系列最后一次作业时间" />
          <el-table-column prop="zCarNo" label="Z车编号" />
          <el-table-column prop="zLastTime" label="Z系列最后一次作业时间" />
          <el-table-column prop="pointDistance" label="点间距离" />
          <el-table-column prop="sampleFile" label="采样文件" />
          <el-table-column prop="notes" label="备注" />
          <el-table-column label="操作" width="180">
            <template #default="scope">
              <el-button type="primary" link @click="handleEditTableRecord(scope.row)">修改</el-button>
              <el-button type="danger" link @click="handleDeleteTableRecord(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="totalRecords"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-dialog>

    <!-- 表格记录编辑对话框 -->
    <el-dialog
      v-model="recordDialogVisible"
      :title="isEditingRecord ? '修改记录' : '新增记录'"
      width="50%"
      :close-on-click-modal="false">
      <el-form :model="recordForm" label-width="160px">
        <el-form-item label="C车编号">
          <el-input v-model="recordForm.cCarNo" />
        </el-form-item>
        <el-form-item label="C系列最后一次采样时间">
          <el-date-picker 
            v-model="recordForm.cLastTime" 
            type="datetime" 
            placeholder="选择日期时间" 
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss" />
        </el-form-item>
        <el-form-item label="H车编号">
          <el-input v-model="recordForm.hCarNo" />
        </el-form-item>
        <el-form-item label="H系列最后一次作业时间">
          <el-date-picker 
            v-model="recordForm.hLastTime" 
            type="datetime" 
            placeholder="选择日期时间" 
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss" />
        </el-form-item>
        <el-form-item label="Z车编号">
          <el-input v-model="recordForm.zCarNo" />
        </el-form-item>
        <el-form-item label="Z系列最后一次作业时间">
          <el-date-picker 
            v-model="recordForm.zLastTime" 
            type="datetime" 
            placeholder="选择日期时间" 
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss" />
        </el-form-item>
        <el-form-item label="点间距离">
          <el-input v-model="recordForm.pointDistance" />
        </el-form-item>
        <el-form-item label="采样文件">
          <el-input v-model="recordForm.sampleFile" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input type="textarea" v-model="recordForm.notes" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="recordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveTableRecord">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 标记组管理对话框 -->
    <el-dialog
      v-model="markerGroupDialogVisible"
      title="标记组管理"
      width="60%"
      :close-on-click-modal="false">
      <div class="marker-group-container">
        <div class="marker-group-toolbar">
          <el-button type="primary" @click="handleAddMarkerGroup">新增标记组</el-button>
        </div>
        <el-table :data="markerGroups" border style="width: 100%">
          <el-table-column prop="name" label="标记组名称" min-width="120" />
          <el-table-column label="颜色" width="100">
            <template #default="scope">
              <div class="color-preview" :style="{ backgroundColor: scope.row.color }"></div>
            </template>
          </el-table-column>
          <el-table-column label="可见性" width="100">
            <template #default="scope">
              <el-switch
                v-model="scope.row.is_visible"
                @change="(val) => toggleMarkerGroupVisibility(scope.row.id, val)"
                :active-value="1"
                :inactive-value="0" />
            </template>
          </el-table-column>
          <el-table-column label="标记数量" width="100">
            <template #default="scope">
              {{ getMarkerCountByGroup(scope.row.id) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="scope">
              <el-button 
                type="primary" 
                link
                @click="handleEditMarkerGroup(scope.row)">
                编辑
              </el-button>
              <el-button 
                type="danger" 
                link
                @click="handleDeleteMarkerGroup(scope.row)">
                删除
              </el-button>
              <el-button 
                type="success" 
                link
                @click="handleViewMarkers(scope.row.id)">
                查看标记
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 标记列表 (当选择查看特定标记组的标记时显示) -->
      <div class="marker-list-container" v-if="showMarkersInGroup">
        <div class="marker-list-header">
          <h3>{{ currentMarkerGroup ? currentMarkerGroup.name : '' }} 标记列表</h3>
          <el-button @click="showMarkersInGroup = false" type="text">返回</el-button>
        </div>
        <el-table :data="markersInGroup" border style="width: 100%">
          <el-table-column prop="marker_number" label="标记序号" width="100" />
          <el-table-column prop="latitude" label="纬度" width="150" />
          <el-table-column prop="longitude" label="经度" width="150" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="scope">
              <el-button 
                type="primary" 
                link
                @click="locateToMarker(scope.row)">
                定位
              </el-button>
              <el-button 
                type="danger" 
                link
                @click="handleDeleteMarker(scope.row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 标记组编辑对话框 -->
    <el-dialog
      v-model="markerGroupEditDialogVisible"
      :title="isEditingMarkerGroup ? '编辑标记组' : '新增标记组'"
      width="40%"
      :close-on-click-modal="false">
      <el-form :model="markerGroupForm" label-width="100px">
        <el-form-item label="标记组名称" required>
          <el-input v-model="markerGroupForm.name" />
        </el-form-item>
        <el-form-item label="标记颜色" required>
          <div class="color-picker-container">
            <div class="color-preview-large" :style="{ backgroundColor: markerGroupForm.color }"></div>
            <el-color-picker v-model="markerGroupForm.color" show-alpha />
          </div>
        </el-form-item>
        <el-form-item label="可见性">
          <el-switch
            v-model="markerGroupForm.is_visible"
            :active-value="1"
            :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="markerGroupEditDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveMarkerGroup">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加标记对话框 -->
    <el-dialog
      v-model="addMarkerDialogVisible"
      title="添加标记"
      width="500px"
      :close-on-click-modal="false">
      <div class="add-marker-form">
        <el-alert
          v-if="isSelectingMarkerLocation"
          title="请在地图上点击选择标记位置"
          type="info"
          :closable="false"
          show-icon />
        
        <el-form v-if="!isSelectingMarkerLocation" :model="markerForm" label-width="120px">
          <el-form-item label="所属标记组" required>
            <el-select v-model="markerForm.group_id" placeholder="请选择标记组">
              <el-option
                v-for="group in markerGroups"
                :key="group.id"
                :label="group.name"
                :value="group.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="标记序号" required>
            <el-input-number v-model="markerForm.marker_number" :min="1" :max="99" />
          </el-form-item>
          <el-form-item label="标记位置">
            <div v-if="markerLocationSelected" class="selected-location">
              <div class="location-info">
                <div>纬度: {{ markerForm.latitude }}</div>
                <div>经度: {{ markerForm.longitude }}</div>
              </div>
            </div>
            <el-button 
              type="primary" 
              @click="startSelectMarkerLocation">
              {{ markerLocationSelected ? '重新选点' : '开始选点' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer" v-if="!isSelectingMarkerLocation">
          <el-button @click="addMarkerDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="saveMarker"
            :disabled="!markerLocationSelected || !markerForm.group_id">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import mapboxgl from 'mapbox-gl'
import { onMounted, ref, computed, nextTick } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Location, Delete } from '@element-plus/icons-vue'
import MapboxDraw from '@mapbox/mapbox-gl-draw'
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css'
import arrowIcon from '@/assets/arrow.png?base64'
import * as turf from '@turf/turf'
import { format } from 'date-fns'
import * as XLSX from 'xlsx'

export default {
  name: 'MapComponent',
  components: {
    Document,
    Location,
    Delete
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
      EXIT: 'exit',      // 驶出点
      WORK: 'work'       // 作业点 - 在作业区域内的普通点
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

    // 添加当前线条宽度状态变量
    const currentLineWidth = ref(2)

    // 添加测距相关状态
    const isMeasuringDistance = ref(false)
    const measurePoints = ref([])
    const measureLine = ref(null)
    const measureDistance = ref(null)

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
          ['==', ['get', 'pointType'], POINT_TYPES.EXIT], 11, // 驶出点尺寸
          ['==', ['get', 'pointType'], POINT_TYPES.WORK], 10, // 作业点尺寸
          8
        ],
        'circle-color': [
          'case',
          ['in', ['get', 'id'], ['literal', Array.from(selectedPoints.value)]], '#FF0000', // 选中的点显示红色
          ['in', ['get', 'id'], ['literal', Array.from(abnormalPoints.value)]], '#FF00FF',
          ['==', ['get', 'pointType'], POINT_TYPES.ENTRY], '#67C23A', // 驶入点绿色
          ['==', ['get', 'pointType'], POINT_TYPES.EXIT], '#E6A23C', // 即将驶出点黄色
          ['==', ['get', 'pointType'], POINT_TYPES.WORK], '#1989FA', // 作业点蓝色
          ['get', 'color']
        ],
            'circle-opacity': [
              'case',
          ['in', ['get', 'id'], ['literal', Array.from(selectedPoints.value)]], 1,
          ['in', ['get', 'id'], ['literal', Array.from(abnormalPoints.value)]], 1,
          ['==', ['get', 'isActive'], true], 1,
          ['==', ['get', 'id'], activePointId.value], 1,
          ['==', ['get', 'pointType'], POINT_TYPES.EXIT], 0.9, // 即将驶出点透明度
          ['==', ['get', 'pointType'], POINT_TYPES.WORK], 0.8, // 作业点透明度
          0.6
            ],
            'circle-stroke-width': [
              'case',
          ['in', ['get', 'id'], ['literal', Array.from(selectedPoints.value)]], 3,
          ['in', ['get', 'id'], ['literal', Array.from(abnormalPoints.value)]], 3,
          ['==', ['get', 'id'], activePointId.value], 3,
          ['==', ['get', 'isActive'], true], 2,
          ['==', ['get', 'pointType'], POINT_TYPES.EXIT], 2.5, // 即将驶出点边框宽度
          ['==', ['get', 'pointType'], POINT_TYPES.WORK], 2, // 作业点边框宽度
          1
            ],
            'circle-stroke-color': [
              'case',
          ['in', ['get', 'id'], ['literal', Array.from(selectedPoints.value)]], '#FFFF00',
          ['in', ['get', 'id'], ['literal', Array.from(abnormalPoints.value)]], '#FFFF00',
              ['==', ['get', 'id'], activePointId.value], '#ffff00',
          ['==', ['get', 'isActive'], true], '#ffffff',
          ['==', ['get', 'pointType'], POINT_TYPES.EXIT], '#CC9900', // 即将驶出点边框颜色
          ['==', ['get', 'pointType'], POINT_TYPES.WORK], '#0066CC', // 作业点边框颜色
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

      // 询问用户是否设置偏移量
      offsetPromptDialogVisible.value = true
    }

    // 处理用户选择不设置偏移量
    const handleOffsetPromptNo = () => {
      offsetPromptDialogVisible.value = false
      // 直接继续上传文件处理流程，无需偏移量
      processFileUpload(false)
    }

    // 处理用户选择设置偏移量
    const handleOffsetPromptYes = () => {
      offsetPromptDialogVisible.value = false
      // 获取车辆设置信息以显示在偏移量设置对话框中
      fetchVehicleSettings().then(() => {
        // 准备上传偏移设置数据
        if (vehicleSettings.value.length > 0) {
          // 从现有车辆设置中获取
          uploaderOffsetData.value = vehicleSettings.value.map(vehicle => ({
            ...vehicle,
            // 确保偏移量是数字类型
            longitude_offset: parseFloat(vehicle.longitude_offset || 0),
            latitude_offset: parseFloat(vehicle.latitude_offset || 0),
            line_width: parseFloat(vehicle.line_width || 2),
            color: vehicle.line_color || vehicle.color || markerColors[0]
          }));
        } else {
          // 创建新的偏移设置
          uploaderOffsetData.value = [{
            id: null,
            vehicle_name: '当前文件',
            longitude_offset: 0,
            latitude_offset: 0,
            line_width: 2,
            line_color: markerColors[0]
          }];
        }
        
        // 显示上传偏移量设置对话框
        uploadOffsetDialogVisible.value = true
      })
    }

    // 取消上传偏移量设置
    const handleUploadOffsetDialogClose = () => {
      uploadOffsetDialogVisible.value = false
      // 用户关闭了设置对话框，不继续上传
    }

    // 确认上传偏移量设置
    const confirmUploadOffset = () => {
      uploadOffsetDialogVisible.value = false
      
      // 确保设置了偏移量的车辆存在有效数据
      if (uploaderOffsetData.value.length > 0) {
        // 输出所有偏移量设置，检查是否有正确的数据
        console.log('All offset data:', JSON.stringify(uploaderOffsetData.value));
        
        const selectedOffset = uploaderOffsetData.value[0];
        // 确保偏移量数据有效
        if (selectedOffset) {
          console.log('Selected offset:', 
            selectedOffset.vehicle_name,
            'longitude:', selectedOffset.longitude_offset, 
            'latitude:', selectedOffset.latitude_offset,
            'fullObject:', JSON.stringify(selectedOffset)
          );
        }
      } else {
        console.log('No offset data available');
      }
      
      // 使用设置的偏移量继续上传
      processFileUpload(true)
    }

    // 添加偏移量行
    const addOffsetRow = () => {
      uploaderOffsetData.value.push({
        id: null,
        vehicle_name: `车辆 ${uploaderOffsetData.value.length + 1}`,
        longitude_offset: 0,
        latitude_offset: 0,
        line_width: 2,
        line_color: markerColors[uploaderOffsetData.value.length % markerColors.length]
      })
    }

    // 移除偏移量行
    const removeOffsetRow = (index) => {
      if (uploaderOffsetData.value.length > 1) {
        uploaderOffsetData.value.splice(index, 1)
      } else {
        ElMessage.warning('至少需要保留一行偏移设置')
      }
    }

    // 应用特定偏移量
    const applySpecificOffset = (offset) => {
      // 将所选偏移移到数组第一位，确保它会被使用
      const index = uploaderOffsetData.value.findIndex(item => 
        item.vehicle_name === offset.vehicle_name &&
        item.longitude_offset === offset.longitude_offset &&
        item.latitude_offset === offset.latitude_offset
      )
      
      if (index !== -1) {
        // 如果找到，将它移到第一位
        const selected = uploaderOffsetData.value.splice(index, 1)[0]
        uploaderOffsetData.value.unshift(selected)
        console.log('Selected offset to apply:', selected.vehicle_name, selected.longitude_offset, selected.latitude_offset)
        
        // 关闭对话框，应用偏移并上传
        uploadOffsetDialogVisible.value = false
        processFileUpload(true)
      }
    }

    // 处理文件上传流程
    const processFileUpload = async (applyOffset = false) => {
      loading.value = true
      const uploadPromises = []
      const newPoints = []
      
      console.log('Process file upload, applyOffset:', applyOffset);
      
      // 获取选中的偏移量设置（如果有）
      let offsetSettings = null;
      if (applyOffset && uploaderOffsetData.value.length > 0) {
        offsetSettings = { ...uploaderOffsetData.value[0] };
        // 确保偏移量是数字类型
        offsetSettings.longitude_offset = parseFloat(offsetSettings.longitude_offset || 0);
        offsetSettings.latitude_offset = parseFloat(offsetSettings.latitude_offset || 0);
      }
        
      console.log('Offset settings to apply:', offsetSettings ? 
        `${offsetSettings.vehicle_name} - lon: ${offsetSettings.longitude_offset}, lat: ${offsetSettings.latitude_offset}` : 
        'No offset');

      try {
        // 先处理所有文件
        for (let i = 0; i < fileList.value.length; i++) {
          const file = fileList.value[i]
          if (file.status === 'ready') {
            const formData = new FormData()
            formData.append('file', file.raw)
            const promise = axios.post('http://localhost:5005/api/waypoints', formData)
              .then(response => {
                const points = response.data.waypoints
                console.log(`Processing file ${file.name}, points: ${points.length}`);
                
                // 确定使用哪种颜色
                let color = markerColors[i % markerColors.length]
                if (applyOffset && offsetSettings) {
                  color = offsetSettings.line_color || offsetSettings.color || color
                }
                
                // 先收集所有点，不急着添加
                points.forEach((point, idx) => {
                  // 确保点的经纬度是数字类型
                  let baseLongitude = parseFloat(point.longitude);
                  let baseLatitude = parseFloat(point.latitude);
                  let newLongitude = baseLongitude;
                  let newLatitude = baseLatitude;
                  
                  // 应用偏移量（如果需要）
                  if (applyOffset && offsetSettings && 
                      (offsetSettings.longitude_offset !== 0 || offsetSettings.latitude_offset !== 0)) {
                    // 记录应用前后的经纬度，用于调试
                    const origLon = newLongitude;
                    const origLat = newLatitude;
                    
                    // 确保进行数字计算
                    newLongitude = parseFloat((baseLongitude + offsetSettings.longitude_offset).toFixed(8));
                    newLatitude = parseFloat((baseLatitude + offsetSettings.latitude_offset).toFixed(8));
                    
                    // 只对前几个点输出日志，避免日志过多
                    if (idx < 3) {
                      console.log(`Point ${idx} offset applied:`, 
                        `lon: ${origLon} -> ${newLongitude} (offset: ${offsetSettings.longitude_offset})`, 
                        `lat: ${origLat} -> ${newLatitude} (offset: ${offsetSettings.latitude_offset})`
                      );
                    }
                  }
                  
                  newPoints.push({
                    ...point,
                    longitude: newLongitude,
                    latitude: newLatitude,
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
            // 前一个点在区域外，当前点在区域内，标记为驶入点
            pointType = POINT_TYPES.ENTRY
          } else if (isInArea && !nextInArea) {
            // 当前点在区域内，下一个点在区域外，标记为驶出点
            pointType = POINT_TYPES.EXIT
          } else if (isInArea) {
            // 在作业区内的普通点标记为作业点
            pointType = POINT_TYPES.WORK
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
          'line-width': currentLineWidth.value, // 使用状态变量而不是硬编码值
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

          // 获取前一个点和后一个点
          const prevPoint = index > 0 ? filePoints[index - 1] : null
          const nextPoint = index < filePoints.length - 1 ? filePoints[index + 1] : null
          
          // 直接计算前后点是否在作业区内
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
            // 当前点在区域内，下一个点在区域外，标记为即将驶出点
            pointType = POINT_TYPES.EXIT
          } else if (isInWorkArea) {
            // 在作业区内的普通点标记为作业点
            pointType = POINT_TYPES.WORK
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
        [POINT_TYPES.NORMAL]: '普通点',
        [POINT_TYPES.WORK]: '作业点'
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
         
          // 获取WMS图层数据
          fetchWmsLayers()
          
          // 获取障碍物数据
          fetchObstacles()
          
          // 加载标记组和标记
          fetchMarkerGroups()
          fetchAllMarkers()
        }
      })
    })

    // 修改为单独的地图初始化函数
    const initMap = () => {
      mapboxgl.accessToken = 'pk.eyJ1IjoiYWlyb25kZXYiLCJhIjoiY2xlaHZ5eDNvMDZpbTN4cXFmY3p0OWs5bSJ9.1_B_7dVoXWRPJ2XErYCnBw'
      
      map = new mapboxgl.Map({
        container: mapContainer.value,
        style: 'mapbox://styles/mapbox/satellite-v9',
        center: [116.397428, 39.90923], // 默认位置：北京
        zoom: 17,
        minZoom: 3,
        maxZoom: 22
      })

      // 添加导航控制
      map.addControl(new mapboxgl.NavigationControl(), 'top-right')
      
      // 添加比例尺
      map.addControl(new mapboxgl.ScaleControl({
        maxWidth: 200,
        unit: 'metric'
      }), 'bottom-left')
      
      // 添加全屏控制
      map.addControl(new mapboxgl.FullscreenControl(), 'top-right')
      
      // 添加定位控制
      map.addControl(new mapboxgl.GeolocateControl({
        positionOptions: {
          enableHighAccuracy: true
        },
        trackUserLocation: true,
        showUserHeading: true
      }), 'top-right')
      
      // 添加绘图工具
      draw.value = new MapboxDraw({
        displayControlsDefault: false,
        controls: {
          polygon: true,
          trash: true
        }
      })
      map.addControl(draw.value, 'top-right')
      
      map.on('load', () => {
        // 初始化点集合图层
        initPointsLayer()
        
        // 加载标记组和标记
        fetchMarkerGroups()
        fetchAllMarkers()
      })
      
      // 监听绘制完成事件
      map.on('draw.create', handleDrawCreate)
      map.on('draw.delete', handleDrawDelete)
      map.on('draw.update', handleDrawUpdate)
    }

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
      // 首先询问用户是否需要设置偏移量
      ElMessageBox.confirm(
        '是否需要为导出的航点设置偏移量？',
        '导出航点',
        {
          confirmButtonText: '是',
          cancelButtonText: '否',
          type: 'info'
        }
      ).then(() => {
        // 用户选择设置偏移量
        showExportOffsetDialog();
      }).catch(() => {
        // 用户选择不设置偏移量，继续常规导出流程
        showExportTypeDialog();
      });
    };

    // 显示导出类型选择对话框
    const showExportTypeDialog = () => {
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
        exportPoints(parseInt(value), null); // 无偏移量
      }).catch(() => {
        // 用户取消操作
      });
    };

    // 显示导出偏移量设置对话框
    const showExportOffsetDialog = () => {
      // 获取车辆设置信息以显示在偏移量设置对话框中
      fetchVehicleSettings().then(() => {
        // 准备导出偏移设置数据
        if (vehicleSettings.value.length > 0) {
          // 从现有车辆设置中获取
          exportOffsetData.value = vehicleSettings.value.map(vehicle => ({
            ...vehicle,
            // 确保偏移量是数字类型
            longitude_offset: parseFloat(vehicle.longitude_offset || 0),
            latitude_offset: parseFloat(vehicle.latitude_offset || 0),
            line_width: parseFloat(vehicle.line_width || 2),
            color: vehicle.line_color || vehicle.color || markerColors[0]
          }));
        } else {
          // 创建新的偏移设置
          exportOffsetData.value = [{
            id: null,
            vehicle_name: '当前导出',
            longitude_offset: 0,
            latitude_offset: 0,
            line_width: 2,
            line_color: markerColors[0]
          }];
        }
        
        // 显示导出偏移量设置对话框
        exportOffsetDialogVisible.value = true;
      });
    };

    // 处理导出偏移量设置对话框关闭
    const handleExportOffsetDialogClose = () => {
      exportOffsetDialogVisible.value = false;
    };

    // 应用特定导出偏移量
    const applyExportOffset = (offset) => {
      // 关闭对话框
      exportOffsetDialogVisible.value = false;
      
      // 记录日志
      console.log('Applying export offset:', 
        offset.vehicle_name,
        'longitude:', offset.longitude_offset, 
        'latitude:', offset.latitude_offset
      );
      
      // 显示导出类型选择对话框，并传递偏移量
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
        exportPoints(parseInt(value), offset);
      }).catch(() => {
        // 用户取消操作
      });
    };

    // 确认导出偏移量
    const confirmExportOffset = () => {
      if (exportOffsetData.value.length > 0) {
        const selectedOffset = exportOffsetData.value[0];
        applyExportOffset(selectedOffset);
      } else {
        ElMessage.warning('没有可用的偏移量设置');
      }
    };

    const exportPoints = async (weedingType, offsetSettings) => {
      try {
        // 按文件分组获取航点
        const groups = {};
        allWaypoints.value.forEach(point => {
          if (!groups[point.fileName]) {
            groups[point.fileName] = [];
          }
          
          // 如果有偏移量设置，则应用偏移
          let pointData = { ...point };
          if (offsetSettings) {
            pointData = {
              ...point,
              longitude: Number((point.longitude + parseFloat(offsetSettings.longitude_offset)).toFixed(8)),
              latitude: Number((point.latitude + parseFloat(offsetSettings.latitude_offset)).toFixed(8))
            };
          }
          
          groups[point.fileName].push(pointData);
        });

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
        };

        // 发送数据到后端
        const response = await axios.post('http://localhost:5005/api/export', exportData);
        if (response.data.success) {
          // 处理每个文件的下载
          response.data.files.forEach(file => {
            // 创建Blob对象
            const blob = new Blob([file.content], { type: 'text/plain' });
            // 创建下载链接
            const downloadLink = document.createElement('a');
            downloadLink.href = URL.createObjectURL(blob);
            downloadLink.download = file.name;
            // 触发下载
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
          });
          
          if (offsetSettings) {
            ElMessage.success(`航点文件导出成功，已应用偏移量 (经度: ${offsetSettings.longitude_offset}°, 纬度: ${offsetSettings.latitude_offset}°)`);
          } else {
            ElMessage.success('航点文件导出成功');
          }
        } else {
          ElMessage.error(response.data.error || '导出失败');
        }
      } catch (error) {
        console.error('Export error:', error);
        ElMessage.error('导出失败：' + (error.response?.data?.error || error.message));
      }
    };

    // 获取点的导出类型
    const getPointExportType = (point) => {
      const feature = pointsData.value.features.find(
        f => f.properties.id === `${point.fileIndex}-${point.index}`
      )
      if (!feature) return 0 // 普通点

      // 检查点是否在作业区内
      if (!feature.properties.inWorkArea) {
        return 0 // 非作业区内的点为普通点
      }

      switch (feature.properties.pointType) {
        case POINT_TYPES.ENTRY:
          return 1 // 驶入点
        case POINT_TYPES.EXIT:
          return 2 // 驶出点
        case POINT_TYPES.WORK:
          return 3 // 作业点
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
    
    // 添加车辆设置相关状态
    const vehicleSettings = ref([])
    const isAddingVehicle = ref(false)
    const editVehicleDialogVisible = ref(false)
    const editVehicleForm = ref({
      id: null,
      vehicle_name: '',
      longitude_offset: 0,
      latitude_offset: 0,
      line_width: 2,
      line_color: '#0000FF'
    })
    
    // 打开偏移量设置对话框
    const handleOffsetPoints = () => {
      offsetDialogVisible.value = true
      // 获取所有车辆设置
      fetchVehicleSettings()
    }
    
    // 获取车辆设置
    const fetchVehicleSettings = async () => {
      try {
        loading.value = true
        const response = await axios.get('http://localhost:5005/api/vehicles')
        //const response = await axios.get('http://localhost:5005/api/vehicles')
        if (response.data.success) {
          vehicleSettings.value = response.data.vehicles
        } else {
          ElMessage.error('获取车辆设置失败：' + response.data.error)
        }
      } catch (error) {
        console.error('Failed to fetch vehicle settings:', error)
        ElMessage.error('获取车辆设置失败：' + error.message)
      } finally {
        loading.value = false
      }
    }

    // 关闭偏移量设置对话框
    const handleOffsetDialogClose = () => {
      offsetDialogVisible.value = false
      isAddingVehicle.value = false
      
      // 重置编辑表单
      editVehicleForm.value = {
        id: null,
        vehicle_name: '',
        longitude_offset: 0,
        latitude_offset: 0,
        line_width: 2,
        line_color: '#0000FF'
      }
    }

    // 开始添加车辆
    const startAddVehicle = () => {
      isAddingVehicle.value = true
      
      // 重置编辑表单
      editVehicleForm.value = {
        id: null,
        vehicle_name: '',
        longitude_offset: 0,
        latitude_offset: 0,
        line_width: 2,
        line_color: '#0000FF'
      }
    }
    
    // 取消添加车辆
    const cancelAddVehicle = () => {
      isAddingVehicle.value = false
    }
    
    // 保存新车辆
    const saveVehicle = async () => {
      try {
        if (!editVehicleForm.value.vehicle_name) {
          ElMessage.warning('请输入车辆名称')
          return
        }
        
        loading.value = true
        const response = await axios.post('http://localhost:5005/api/vehicles', editVehicleForm.value)
        //const response = await axios.post('http://localhost:5005/api/vehicles', editVehicleForm.value)
        
        if (response.data.success) {
          ElMessage.success('车辆添加成功')
          // 刷新车辆列表
          fetchVehicleSettings()
          // 重置添加状态
          isAddingVehicle.value = false
        } else {
          ElMessage.error('添加车辆失败：' + response.data.error)
        }
      } catch (error) {
        console.error('Failed to add vehicle:', error)
        ElMessage.error('添加车辆失败：' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    // 编辑车辆
    const handleEditVehicle = (vehicle) => {
      editVehicleForm.value = { ...vehicle }
      editVehicleDialogVisible.value = true
    }
    
    // 更新车辆
    const updateVehicle = async () => {
      try {
        if (!editVehicleForm.value.vehicle_name) {
          ElMessage.warning('请输入车辆名称')
          return
        }
        
        loading.value = true
        const response = await axios.put(
          `http://localhost:5005/api/vehicles/${editVehicleForm.value.id}`, 
          editVehicleForm.value
        )
        //const response = await axios.put(
        //  `http://localhost:5005/api/vehicles/${editVehicleForm.value.id}`, 
        //  editVehicleForm.value
        //)
        
        if (response.data.success) {
          ElMessage.success('车辆更新成功')
          // 刷新车辆列表
          fetchVehicleSettings()
          // 关闭编辑对话框
          editVehicleDialogVisible.value = false
        } else {
          ElMessage.error('更新车辆失败：' + response.data.error)
        }
      } catch (error) {
        console.error('Failed to update vehicle:', error)
        ElMessage.error('更新车辆失败：' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    // 删除车辆
    const handleDeleteVehicle = (vehicle) => {
      ElMessageBox.confirm(
        `确定要删除车辆 "${vehicle.vehicle_name}" 吗？`,
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          loading.value = true
          //const response = await axios.delete(`http://localhost:5005/api/vehicles/${vehicle.id}`)
          const response = await axios.delete(`http://localhost:5005/api/vehicles/${vehicle.id}`)
          
          if (response.data.success) {
            ElMessage.success('车辆删除成功')
            // 刷新车辆列表
            fetchVehicleSettings()
          } else {
            ElMessage.error('删除车辆失败：' + response.data.error)
          }
        } catch (error) {
          console.error('Failed to delete vehicle:', error)
          ElMessage.error('删除车辆失败：' + error.message)
        } finally {
          loading.value = false
        }
      }).catch(() => {
        // 用户取消删除
      })
    }
    
    // 确认使用选中车辆的偏移设置
    const handleConfirmOffset = (vehicle) => {
      ElMessageBox.confirm(
        `确定要使用车辆 "${vehicle.vehicle_name}" 的偏移设置吗？`,
        '确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        // 应用偏移量和线条样式
        applyVehicleOffset(vehicle)
      }).catch(() => {
        // 用户取消操作
      })
    }
    
    // 应用车辆偏移量和线条样式
    const applyVehicleOffset = async (vehicle) => {
      const { id, longitude_offset, latitude_offset, line_color, line_width } = vehicle
      
      // 更新当前线条宽度
      currentLineWidth.value = line_width
      
      // 更新所有航点的经纬度
      allWaypoints.value = allWaypoints.value.map(point => ({
        ...point,
        longitude: Number((point.longitude + longitude_offset).toFixed(8)),
        latitude: Number((point.latitude + latitude_offset).toFixed(8)),
        color: line_color // 更新颜色
      }))
      
      // 更新地图点位
      pointsData.value.features = pointsData.value.features.map(feature => ({
        ...feature,
        geometry: {
          ...feature.geometry,
          coordinates: [
            Number((feature.geometry.coordinates[0] + longitude_offset).toFixed(8)),
            Number((feature.geometry.coordinates[1] + latitude_offset).toFixed(8))
          ]
        },
        properties: {
          ...feature.properties,
          color: line_color // 更新颜色
        }
      }))
      
      // 更新地图显示
      updatePointsLayer()
      updateLinesLayer()
      
      // 记录偏移量设置历史
      try {
        await axios.post('http://localhost:5005/api/offset/history', {
          vehicle_id: id,
          longitude_offset,
          latitude_offset,
          notes: `应用了车辆 "${vehicle.vehicle_name}" 的偏移设置`
        })
        console.log('Offset history recorded successfully')
      } catch (error) {
        console.error('Failed to record offset history:', error)
      }
      
      // 关闭对话框并提示
      handleOffsetDialogClose()
      ElMessage.success(`已应用车辆 "${vehicle.vehicle_name}" 的偏移设置和样式`)
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
      
      // 显示删除成功消息
      ElMessage.success(`已删除 ${selectedPoints.value.size} 个点`)
      
      // 自动执行航点合并操作
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

      ElMessage.success('框选删除后已自动完成航点合并')
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
    
    // 添加此函数修复引用错误
    const updatePointsInWorkArea = () => {
      if (workAreas.value.length > 0) {
        updateWorkAreaPoints()
      }
    }

    // 添加WMS图层管理相关状态
    const wmsLayers = ref([]) // 存储所有WMS图层
    const showWmsLayersMenu = ref(false) // 控制WMS图层菜单显示
    const wmsManagerDialogVisible = ref(false) // 控制WMS图层管理对话框显示
    const isAddingWmsLayer = ref(false) // 是否在添加新WMS图层
    const editWmsLayerDialogVisible = ref(false) // 控制编辑WMS图层对话框显示
    const editWmsLayerForm = ref({
      id: null,
      name: '',
      url: '',
      layer_id: '',
      opacity: 0.8,
      enabled: true
    })
    
    // 获取所有WMS图层
    const fetchWmsLayers = async () => {
      try {
        loading.value = true
        const response = await axios.get('http://localhost:5005/api/wms/layers')
        if (response.data.success) {
          wmsLayers.value = response.data.layers
          // 加载启用的WMS图层
          loadEnabledWmsLayers()
        } else {
          ElMessage.error('获取WMS图层失败：' + response.data.error)
        }
      } catch (error) {
        console.error('Failed to fetch WMS layers:', error)
        ElMessage.error('获取WMS图层失败：' + error.message)
      } finally {
        loading.value = false
      }
    }

    // 切换WMS图层显示状态
    const toggleWmsLayer = async (layerId, enabled) => {
      try {
        loading.value = true
        const response = await axios.put(`http://localhost:5005/api/wms/layers/${layerId}/toggle`, {
          enabled
        })
        
        if (response.data.success) {
          // 更新本地状态
          const layerIndex = wmsLayers.value.findIndex(l => l.id === layerId)
          if (layerIndex !== -1) {
            wmsLayers.value[layerIndex].enabled = enabled
          }
          
          // 刷新地图WMS图层
          loadEnabledWmsLayers()
          
          ElMessage.success(`图层已${enabled ? '启用' : '禁用'}`)
        } else {
          ElMessage.error('图层状态更新失败：' + response.data.error)
        }
      } catch (error) {
        console.error('Failed to toggle WMS layer:', error)
        ElMessage.error('图层状态更新失败：' + error.message)
      } finally {
        loading.value = false
      }
    }

    // 加载所有启用的WMS图层
    const loadEnabledWmsLayers = () => {
      if (!map) return
      
      // 移除现有的WMS图层
      wmsLayers.value.forEach(layer => {
        const layerId = `wms-layer-${layer.id}`
        if (map.getLayer(layerId)) {
          map.removeLayer(layerId)
        }
        if (map.getSource(layerId)) {
          map.removeSource(layerId)
        }
      })
      
      // 添加启用的WMS图层
      wmsLayers.value.filter(layer => layer.enabled).forEach(layer => {
        const layerId = `wms-layer-${layer.id}`
        
        map.addSource(layerId, {
          'type': 'raster',
          'tiles': [
            `${layer.url}?` +
            'SERVICE=WMS' +
            '&VERSION=1.1.1' +
            '&REQUEST=GetMap' +
            '&FORMAT=image/png' +
            '&TRANSPARENT=true' +
            `&LAYERS=${layer.layer_id}` +
            '&exceptions=application/vnd.ogc.se_inimage' +
            '&SRS=EPSG:3857' +
            '&STYLES=' +
            '&WIDTH=256' +
            '&HEIGHT=256' +
            '&BBOX={bbox-epsg-3857}'
          ],
          'tileSize': 256
        })

        // 添加WMS图层到地图，放在点图层下面
        map.addLayer({
          'id': layerId,
          'type': 'raster',
          'source': layerId,
          'paint': {
            'raster-opacity': layer.opacity
          },
          'layout': {
            'visibility': 'visible'
          }
        }, map.getLayer('points-circle') ? 'points-circle' : undefined)
      })
    }

    // 打开WMS图层管理对话框
    const handleOpenWmsLayerManager = () => {
      wmsManagerDialogVisible.value = true
      showWmsLayersMenu.value = false // 关闭图层菜单
    }

    // 开始添加WMS图层
    const startAddWmsLayer = () => {
      isAddingWmsLayer.value = true
      
      // 重置编辑表单
      editWmsLayerForm.value = {
        id: null,
        name: '',
        url: '',
        layer_id: '',
        opacity: 0.8,
        enabled: true
      }
    }
    
    // 取消添加WMS图层
    const cancelAddWmsLayer = () => {
      isAddingWmsLayer.value = false
    }
    
    // 保存新WMS图层
    const saveWmsLayer = async () => {
      try {
        const { name, url, layer_id } = editWmsLayerForm.value
        
        if (!name || !url || !layer_id) {
          ElMessage.warning('请填写必填字段')
          return
        }
        
        loading.value = true
        const response = await axios.post('http://localhost:5005/api/wms/layers', editWmsLayerForm.value)
        
        if (response.data.success) {
          ElMessage.success('WMS图层添加成功')
          // 刷新图层列表
          fetchWmsLayers()
          // 重置添加状态
          isAddingWmsLayer.value = false
        } else {
          ElMessage.error('添加WMS图层失败：' + response.data.error)
        }
      } catch (error) {
        console.error('Failed to add WMS layer:', error)
        ElMessage.error('添加WMS图层失败：' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    // 编辑WMS图层
    const handleEditWmsLayer = (layer) => {
      editWmsLayerForm.value = { ...layer }
      editWmsLayerDialogVisible.value = true
    }
    
    // 更新WMS图层
    const updateWmsLayer = async () => {
      try {
        const { id, name, url, layer_id } = editWmsLayerForm.value
        
        if (!name || !url || !layer_id) {
          ElMessage.warning('请填写必填字段')
          return
        }
        
        loading.value = true
        const response = await axios.put(
          `http://localhost:5005/api/wms/layers/${id}`, 
          editWmsLayerForm.value
        )
        
        if (response.data.success) {
          ElMessage.success('WMS图层更新成功')
          // 刷新图层列表
          fetchWmsLayers()
          // 关闭编辑对话框
          editWmsLayerDialogVisible.value = false
        } else {
          ElMessage.error('更新WMS图层失败：' + response.data.error)
        }
      } catch (error) {
        console.error('Failed to update WMS layer:', error)
        ElMessage.error('更新WMS图层失败：' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    // 删除WMS图层
    const handleDeleteWmsLayer = (layer) => {
      ElMessageBox.confirm(
        `确定要删除图层 "${layer.name}" 吗？`,
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          loading.value = true
          const response = await axios.delete(`http://localhost:5005/api/wms/layers/${layer.id}`)
          
          if (response.data.success) {
            ElMessage.success('WMS图层删除成功')
            // 刷新图层列表
            fetchWmsLayers()
          } else {
            ElMessage.error('删除WMS图层失败：' + response.data.error)
          }
        } catch (error) {
          console.error('Failed to delete WMS layer:', error)
          ElMessage.error('删除WMS图层失败：' + error.message)
        } finally {
          loading.value = false
        }
      }).catch(() => {
        // 用户取消删除
      })
    }

    // 历史记录相关数据
    const offsetHistoryDialogVisible = ref(false)
    const offsetHistoryRecords = ref([])
    const historyLoading = ref(false)
    const historyCurrentPage = ref(1)
    const historyPageSize = ref(10)
    const historyTotalCount = ref(0)

    // 偏移量历史记录相关函数
    const showOffsetHistoryDialog = () => {
      offsetHistoryDialogVisible.value = true
      fetchOffsetHistory()
    }

    const fetchOffsetHistory = async () => {
      try {
        historyLoading.value = true
        const response = await axios.get(`http://localhost:5005/api/offset/history?page=${historyCurrentPage.value}&page_size=${historyPageSize.value}`)
        
        if (response.data.success) {
          offsetHistoryRecords.value = response.data.history.records
          historyTotalCount.value = response.data.history.total
        } else {
          ElMessage.error('获取偏移量历史记录失败：' + response.data.error)
        }
      } catch (error) {
        console.error('Failed to fetch offset history:', error)
        ElMessage.error('获取偏移量历史记录失败：' + error.message)
      } finally {
        historyLoading.value = false
      }
    }

    const handleHistoryPageChange = (page) => {
      historyCurrentPage.value = page
      fetchOffsetHistory()
    }

    // 格式化时间戳
    const formatTimestamp = (timestamp) => {
      try {
        return format(new Date(timestamp), 'yyyy-MM-dd HH:mm:ss')
      } catch (e) {
        return timestamp
      }
    }

    // 添加障碍物相关状态
    const obstacles = ref([])
    const obstacleDialogVisible = ref(false)
    const obstacleListDialogVisible = ref(false)
    const isDrawingObstacle = ref(false)
    const editingObstacle = ref(null)
    const obstacleForm = ref({
      name: '',
      area: 0,
      height: 2,
      color: '#FF0000',
      coordinates: []
    })
    
    // 获取所有障碍物
    const fetchObstacles = async () => {
      try {
        loading.value = true
        const response = await axios.get('http://localhost:5005/api/obstacles')
        if (response.data.success) {
          obstacles.value = response.data.obstacles
          // 加载障碍物到地图
          loadObstacles()
        } else {
          ElMessage.error('获取障碍物数据失败：' + response.data.error)
        }
      } catch (error) {
        console.error('Failed to fetch obstacles:', error)
        ElMessage.error('获取障碍物数据失败：' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    // 加载障碍物到地图
    const loadObstacles = () => {
      if (!map) return
      
      // 移除现有的障碍物图层
      if (map.getLayer('obstacles-fill')) {
        map.removeLayer('obstacles-fill')
      }
      if (map.getLayer('obstacles-outline')) {
        map.removeLayer('obstacles-outline')
      }
      if (map.getSource('obstacles')) {
        map.removeSource('obstacles')
      }
      
      // 创建障碍物特征集合
      const features = obstacles.value.map(obstacle => ({
        type: 'Feature',
        properties: {
          id: obstacle.id,
          name: obstacle.name,
          height: obstacle.height,
          color: obstacle.color
        },
        geometry: {
          type: 'Polygon',
          coordinates: obstacle.coordinates
        }
      }))
      
      // 添加障碍物数据源
      map.addSource('obstacles', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features
        }
      })
      
      // 添加障碍物填充图层
      map.addLayer({
        id: 'obstacles-fill',
        type: 'fill',
        source: 'obstacles',
        paint: {
          'fill-color': ['get', 'color'],
          'fill-opacity': 0.5
        }
      })
      
      // 添加障碍物边框图层
      map.addLayer({
        id: 'obstacles-outline',
        type: 'line',
        source: 'obstacles',
        paint: {
          'line-color': '#000',
          'line-width': 2
        }
      })
      
      // 添加点击事件监听
      map.on('click', 'obstacles-fill', handleObstacleClick)
    }
    
    // 处理障碍物点击事件
    const handleObstacleClick = (e) => {
      if (isDrawingObstacle.value) return
      
      const feature = e.features[0]
      const obstacleId = feature.properties.id
      
      // 获取完整的障碍物数据
      const obstacle = obstacles.value.find(o => o.id === obstacleId)
      if (obstacle) {
        // 将多边形置于编辑状态
        editObstacle(obstacle)
      }
    }
    
    // 编辑障碍物
    const editObstacle = (obstacle) => {
      editingObstacle.value = obstacle
      
      // 复制现有数据到表单
      obstacleForm.value = {
        name: obstacle.name,
        area: obstacle.area,
        height: obstacle.height,
        color: obstacle.color,
        coordinates: obstacle.coordinates
      }
      
      // 使用draw工具绘制原有多边形
      // 清除现有的所有绘制
      draw.value.deleteAll()
      
      // 添加障碍物多边形到绘图工具
      const obstacleFeature = {
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'Polygon',
          coordinates: obstacle.coordinates
        }
      }
      const ids = draw.value.add(obstacleFeature)
      
      // 设置为编辑模式
      if (ids.length > 0) {
        draw.value.changeMode('direct_select', { featureId: ids[0] })
      }
      
      // 显示编辑对话框
      obstacleDialogVisible.value = true
    }
    
    // 处理障碍物绘制
    const handleObstacleDrawing = () => {
      if (isDrawingObstacle.value) {
        // 取消绘制
        cancelObstacleDrawing()
      } else {
        // 开始绘制
        startObstacleDrawing()
      }
    }
    
    // 开始绘制障碍物
    const startObstacleDrawing = () => {
      isDrawingObstacle.value = true
      
      // 重置表单
      obstacleForm.value = {
        name: '新障碍物',
        area: 0,
        height: 2,
        color: '#FF0000',
        coordinates: []
      }
      
      // 清除现有的所有绘制
      draw.value.deleteAll()
      
      // 设置为多边形绘制模式
      draw.value.changeMode('draw_polygon')
      
      // 添加提示
      ElMessage({
        message: '请在地图上绘制障碍物多边形',
        type: 'info',
        duration: 0,
        showClose: true
      })
      
      // 添加绘制完成事件监听
      map.once('draw.create', handleObstacleDrawComplete)
    }
    
    // 处理障碍物绘制完成
    const handleObstacleDrawComplete = (e) => {
      const polygon = e.features[0]
      
      // 计算面积（平方米）
      const area = turf.area(polygon)
      
      // 获取多边形坐标
      const coordinates = polygon.geometry.coordinates
      
      // 更新表单数据
      obstacleForm.value.area = area
      obstacleForm.value.coordinates = coordinates
      
      // 显示表单对话框
      obstacleDialogVisible.value = true
      
      // 重置绘制状态
      isDrawingObstacle.value = false
      
      // 关闭提示
      ElMessage.closeAll()
    }
    
    // 取消障碍物绘制
    const cancelObstacleDrawing = () => {
      isDrawingObstacle.value = false
      
      // 清除绘制
      draw.value.deleteAll()
      
      // 重置绘图模式
      draw.value.changeMode('simple_select')
      
      // 关闭提示
      ElMessage.closeAll()
    }
    
    // 保存障碍物
    const saveObstacle = async () => {
      try {
        if (!obstacleForm.value.name) {
          ElMessage.warning('请输入障碍物名称')
          return
        }
        
        loading.value = true
        
        if (editingObstacle.value) {
          // 更新现有障碍物
          const response = await axios.put(
            `http://localhost:5005/api/obstacles/${editingObstacle.value.id}`, 
            obstacleForm.value
          )
          
          if (response.data.success) {
            ElMessage.success('障碍物更新成功')
            // 清除编辑状态
            editingObstacle.value = null
          } else {
            ElMessage.error('更新障碍物失败：' + response.data.error)
          }
        } else {
          // 添加新障碍物
          const response = await axios.post(
            'http://localhost:5005/api/obstacles', 
            obstacleForm.value
          )
          
          if (response.data.success) {
            ElMessage.success('障碍物添加成功')
          } else {
            ElMessage.error('添加障碍物失败：' + response.data.error)
          }
        }
        
        // 刷新障碍物列表
        fetchObstacles()
        
        // 关闭对话框
        obstacleDialogVisible.value = false
        
        // 清除绘制
        draw.value.deleteAll()
      } catch (error) {
        console.error('Failed to save obstacle:', error)
        ElMessage.error('保存障碍物失败：' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    // 关闭障碍物对话框
    const handleObstacleDialogClose = () => {
      obstacleDialogVisible.value = false
      editingObstacle.value = null
      
      // 清除绘制
      draw.value.deleteAll()
    }
    
    // 显示障碍物列表对话框
    const showObstacleListDialog = () => {
      obstacleListDialogVisible.value = true
      fetchObstacles()
    }
    
    // 定位到障碍物
    const locateObstacle = (obstacle) => {
      if (!obstacle.coordinates || obstacle.coordinates.length === 0) return
      
      // 计算多边形的中心点
      const polygon = turf.polygon(obstacle.coordinates)
      const center = turf.center(polygon)
      
      // 飞行到中心点
      map.flyTo({
        center: center.geometry.coordinates,
        zoom: 20,
        duration: 1000
      })
      
      // 关闭对话框
      obstacleListDialogVisible.value = false
    }
    
    // 删除障碍物
    const deleteObstacle = (obstacle) => {
      ElMessageBox.confirm(
        `确定要删除障碍物 "${obstacle.name}" 吗？`,
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          loading.value = true
          const response = await axios.delete(`http://localhost:5005/api/obstacles/${obstacle.id}`)
          
          if (response.data.success) {
            ElMessage.success('障碍物删除成功')
            // 刷新障碍物列表
            fetchObstacles()
          } else {
            ElMessage.error('删除障碍物失败：' + response.data.error)
          }
        } catch (error) {
          console.error('Failed to delete obstacle:', error)
          ElMessage.error('删除障碍物失败：' + error.message)
        } finally {
          loading.value = false
        }
      }).catch(() => {
        // 用户取消删除
      })
    }

    // 添加航点偏移量设置提示对话框
    const offsetPromptDialogVisible = ref(false)
    const uploadOffsetDialogVisible = ref(false)
    const uploaderOffsetData = ref([])

    // 导出偏移量设置数据
    const exportOffsetData = ref([])
    const exportOffsetDialogVisible = ref(false)

    // 添加导出偏移量行
    const addExportOffsetRow = () => {
      exportOffsetData.value.push({
        id: null,
        vehicle_name: `车辆 ${exportOffsetData.value.length + 1}`,
        longitude_offset: 0,
        latitude_offset: 0,
        line_width: 2,
        line_color: markerColors[exportOffsetData.value.length % markerColors.length]
      });
    };

    // 移除导出偏移量行
    const removeExportOffsetRow = (index) => {
      if (exportOffsetData.value.length > 1) {
        exportOffsetData.value.splice(index, 1);
      } else {
        ElMessage.warning('至少需要保留一行偏移设置');
      }
    };

    // 添加测距工具相关函数
    const handleMeasureDistance = () => {
      if (isMeasuringDistance.value) {
        // 如果已经在测距模式，取消测距
        cancelMeasureDistance()
      } else {
        // 启用测距模式
        startMeasureDistance()
      }
    }

    const startMeasureDistance = () => {
      isMeasuringDistance.value = true
      measurePoints.value = []
      measureDistance.value = null
      
      // 修改鼠标样式
      map.getCanvas().style.cursor = 'crosshair'
      
      // 添加提示
      ElMessage({
        message: '请在地图上点击选择起点',
        type: 'info',
        duration: 0,
        showClose: true
      })
      
      // 添加地图点击事件
      map.once('click', handleFirstMeasurePoint)
    }

    const handleFirstMeasurePoint = (e) => {
      // 保存第一个点的坐标
      const point = [e.lngLat.lng, e.lngLat.lat]
      measurePoints.value = [point]
      
      // 添加起点标记
      if (!map.getSource('measure-points')) {
        map.addSource('measure-points', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: []
          }
        })
        
        map.addLayer({
          id: 'measure-points-circle',
          type: 'circle',
          source: 'measure-points',
          paint: {
            'circle-radius': 6,
            'circle-color': '#FFFF00',
            'circle-stroke-width': 2,
            'circle-stroke-color': '#000000'
          }
        })
      }
      
      // 更新点位数据
      map.getSource('measure-points').setData({
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: point
            },
            properties: {
              id: 'start'
            }
          }
        ]
      })
      
      // 显示提示选择终点
      ElMessage.closeAll()
      ElMessage({
        message: '请在地图上点击选择终点',
        type: 'info',
        duration: 0,
        showClose: true
      })
      
      // 添加地图点击事件
      map.once('click', handleSecondMeasurePoint)
    }

    const handleSecondMeasurePoint = (e) => {
      // 保存第二个点的坐标
      const point = [e.lngLat.lng, e.lngLat.lat]
      measurePoints.value.push(point)
      
      // 添加终点标记和连线
      if (!map.getSource('measure-line')) {
        map.addSource('measure-line', {
          type: 'geojson',
          data: {
            type: 'Feature',
            geometry: {
              type: 'LineString',
              coordinates: []
            },
            properties: {}
          }
        })
        
        map.addLayer({
          id: 'measure-line-layer',
          type: 'line',
          source: 'measure-line',
          layout: {
            'line-join': 'round',
            'line-cap': 'round'
          },
          paint: {
            'line-color': '#FFFF00',
            'line-width': 3,
            'line-dasharray': [2, 1]
          }
        })
      }
      
      // 更新点位数据
      map.getSource('measure-points').setData({
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: measurePoints.value[0]
            },
            properties: {
              id: 'start'
            }
          },
          {
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: point
            },
            properties: {
              id: 'end'
            }
          }
        ]
      })
      
      // 更新线数据
      map.getSource('measure-line').setData({
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: measurePoints.value
        },
        properties: {}
      })
      
      // 计算距离
      const from = turf.point(measurePoints.value[0])
      const to = turf.point(measurePoints.value[1])
      const distance = turf.distance(from, to, { units: 'meters' })
      measureDistance.value = distance.toFixed(3)
      
      // 显示距离
      ElMessage.closeAll()
      ElMessage({
        message: `测量距离: ${measureDistance.value} 米`,
        type: 'success',
        duration: 0,
        showClose: true
      })
      
      // 重置鼠标样式
      map.getCanvas().style.cursor = ''
      
      // 添加重新测量按钮
      ElMessageBox.confirm(
        `测量距离: ${measureDistance.value} 米`,
        '测距结果',
        {
          confirmButtonText: '重新测量',
          cancelButtonText: '完成',
          type: 'info'
        }
      ).then(() => {
        // 重新测量
        startMeasureDistance()
      }).catch(() => {
        // 完成测量
        cancelMeasureDistance()
      })
    }

    const cancelMeasureDistance = () => {
      isMeasuringDistance.value = false
      measurePoints.value = []
      
      // 重置鼠标样式
      map.getCanvas().style.cursor = ''
      
      // 移除地图图层
      if (map.getLayer('measure-points-circle')) {
        map.removeLayer('measure-points-circle')
      }
      if (map.getLayer('measure-line-layer')) {
        map.removeLayer('measure-line-layer')
      }
      if (map.getSource('measure-points')) {
        map.removeSource('measure-points')
      }
      if (map.getSource('measure-line')) {
        map.removeSource('measure-line')
      }
      
      // 关闭提示
      ElMessage.closeAll()
    }

    // Table management data
    const tableManagementDialogVisible = ref(false)
    const recordDialogVisible = ref(false)
    const isEditingRecord = ref(false)
    const tableRecords = ref([])
    const currentPage = ref(1)
    const pageSize = ref(10)
    const totalRecords = ref(0)
    const recordForm = ref({
      id: null,
      cCarNo: '',
      cLastTime: '',
      hCarNo: '',
      hLastTime: '',
      zCarNo: '',
      zLastTime: '',
      pointDistance: '',
      sampleFile: '',
      notes: ''
    })

    // Fetch table records from the API
    const fetchTableRecords = async () => {
      try {
        const response = await axios.get(`http://localhost:5005/api/tables?page=${currentPage.value}&page_size=${pageSize.value}`)
        if (response.data.success) {
          tableRecords.value = response.data.data.records.map(record => ({
            id: record.id,
            cCarNo: record.c_car_no,
            cLastTime: record.c_last_time,
            hCarNo: record.h_car_no,
            hLastTime: record.h_last_time,
            zCarNo: record.z_car_no,
            zLastTime: record.z_last_time,
            pointDistance: record.point_distance,
            sampleFile: record.sample_file,
            notes: record.notes
          }))
          totalRecords.value = response.data.data.total
        } else {
          ElMessage.error(response.data.error || '获取记录失败')
        }
      } catch (error) {
        console.error('Error fetching table records:', error)
        ElMessage.error('获取记录失败: ' + (error.response?.data?.error || error.message))
      }
    }

    // Show the table management dialog
    const showTableManagementDialog = () => {
      tableManagementDialogVisible.value = true
      fetchTableRecords()
    }

    // Handle page size change
    const handleSizeChange = (newSize) => {
      pageSize.value = newSize
      fetchTableRecords()
    }

    // Handle current page change
    const handleCurrentChange = (newPage) => {
      currentPage.value = newPage
      fetchTableRecords()
    }

    // Handle adding a new table record
    const handleAddTableRecord = () => {
      isEditingRecord.value = false
      recordForm.value = {
        id: null,
        cCarNo: '',
        cLastTime: '',
        hCarNo: '',
        hLastTime: '',
        zCarNo: '',
        zLastTime: '',
        pointDistance: '',
        sampleFile: '',
        notes: ''
      }
      recordDialogVisible.value = true
    }

    // Handle editing a table record
    const handleEditTableRecord = (row) => {
      isEditingRecord.value = true
      recordForm.value = {
        id: row.id,
        cCarNo: row.cCarNo,
        cLastTime: row.cLastTime,
        hCarNo: row.hCarNo,
        hLastTime: row.hLastTime,
        zCarNo: row.zCarNo,
        zLastTime: row.zLastTime,
        pointDistance: row.pointDistance,
        sampleFile: row.sampleFile,
        notes: row.notes
      }
      recordDialogVisible.value = true
    }

    // Save a table record (create or update)
    const saveTableRecord = async () => {
      try {
        const record = {
          c_car_no: recordForm.value.cCarNo,
          c_last_time: recordForm.value.cLastTime,
          h_car_no: recordForm.value.hCarNo,
          h_last_time: recordForm.value.hLastTime,
          z_car_no: recordForm.value.zCarNo,
          z_last_time: recordForm.value.zLastTime,
          point_distance: recordForm.value.pointDistance,
          sample_file: recordForm.value.sampleFile,
          notes: recordForm.value.notes
        }
        
        let response
        if (isEditingRecord.value) {
          // Update existing record
          response = await axios.put(`http://localhost:5005/api/tables/${recordForm.value.id}`, record)
        } else {
          // Create new record
          response = await axios.post('http://localhost:5005/api/tables', record)
        }
        
        if (response.data.success) {
          ElMessage.success(isEditingRecord.value ? '记录更新成功' : '记录添加成功')
          recordDialogVisible.value = false
          fetchTableRecords()
        } else {
          ElMessage.error(response.data.error || '保存记录失败')
        }
      } catch (error) {
        console.error('Error saving table record:', error)
        ElMessage.error('保存记录失败: ' + (error.response?.data?.error || error.message))
      }
    }

    // Handle deleting a table record
    const handleDeleteTableRecord = (row) => {
      ElMessageBox.confirm(
        '确定要删除这条记录吗？',
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      ).then(async () => {
        try {
          const response = await axios.delete(`http://localhost:5005/api/tables/${row.id}`)
          if (response.data.success) {
            ElMessage.success('记录删除成功')
            fetchTableRecords()
          } else {
            ElMessage.error(response.data.error || '删除记录失败')
          }
        } catch (error) {
          console.error('Error deleting table record:', error)
          ElMessage.error('删除记录失败: ' + (error.response?.data?.error || error.message))
        }
      }).catch(() => {
        // User cancelled, do nothing
      })
    }

    // Export table records to Excel
    const exportToExcel = async () => {
      try {
        // Fetch all records for export
        const response = await axios.get('http://localhost:5005/api/tables/export')
        if (response.data.success) {
          const records = response.data.data.map(record => ({
            '作业行号': record.id,
            'C车编号': record.c_car_no,
            'C系列最后一次采样时间': record.c_last_time,
            'H车编号': record.h_car_no,
            'H系列最后一次作业时间': record.h_last_time,
            'Z车编号': record.z_car_no,
            'Z系列最后一次作业时间': record.z_last_time,
            '点间距离': record.point_distance,
            '采样文件': record.sample_file,
            '备注': record.notes
          }))
          
          // Create worksheet
          const worksheet = XLSX.utils.json_to_sheet(records)
          
          // Create workbook
          const workbook = XLSX.utils.book_new()
          XLSX.utils.book_append_sheet(workbook, worksheet, '协和成地块作业地块')
          
          // Generate Excel file
          XLSX.writeFile(workbook, '协和成地块作业地块.xlsx')
          
          ElMessage.success('导出Excel成功')
        } else {
          ElMessage.error(response.data.error || '导出Excel失败')
        }
      } catch (error) {
        console.error('Error exporting to Excel:', error)
        ElMessage.error('导出Excel失败: ' + (error.response?.data?.error || error.message))
      }
    }

    // 标记组管理相关状态
    const markerGroupDialogVisible = ref(false)
    const markerGroupEditDialogVisible = ref(false)
    const markerGroups = ref([])
    const showMarkersInGroup = ref(false)
    const currentMarkerGroup = ref(null)
    const markersInGroup = ref([])
    const isEditingMarkerGroup = ref(false)
    const markerGroupForm = ref({
      id: null,
      name: '',
      color: '#FF0000',
      is_visible: 1
    })

    // 添加标记对话框相关状态
    const addMarkerDialogVisible = ref(false)
    const isSelectingMarkerLocation = ref(false)
    const markerForm = ref({
      group_id: null,
      marker_number: 1,
      latitude: null,
      longitude: null
    })
    const markerLocationSelected = ref(false)
    const temporaryMarker = ref(null)

    // 标记组和标记的存储结构
    const markers = ref([])
    const markerLayers = ref({}) // 用于存储marker对象，便于操作

    // 显示标记组管理对话框
    const showMarkerGroupDialog = () => {
      markerGroupDialogVisible.value = true
      fetchMarkerGroups()
    }

    // 获取所有标记组
    const fetchMarkerGroups = async () => {
      try {
        loading.value = true
        const response = await axios.get('http://localhost:5005/api/marker-groups')
        loading.value = false

        if (response.data.success) {
          markerGroups.value = response.data.groups
        } else {
          ElMessage.error('获取标记组失败：' + response.data.error)
        }
      } catch (error) {
        loading.value = false
        console.error('Error fetching marker groups:', error)
        ElMessage.error('获取标记组失败: ' + (error.response?.data?.error || error.message))
      }
    }

    // 获取特定组的标记数量
    const getMarkerCountByGroup = (groupId) => {
      return markers.value.filter(m => m.group_id === groupId).length
    }

    // 显示指定标记组的标记
    const handleViewMarkers = async (groupId) => {
      try {
        loading.value = true
        const response = await axios.get(`http://localhost:5005/api/markers?group_id=${groupId}`)
        loading.value = false

        if (response.data.success) {
          markersInGroup.value = response.data.markers
          currentMarkerGroup.value = markerGroups.value.find(g => g.id === groupId)
          showMarkersInGroup.value = true
        } else {
          ElMessage.error('获取标记失败：' + response.data.error)
        }
      } catch (error) {
        loading.value = false
        console.error('Error fetching markers:', error)
        ElMessage.error('获取标记失败: ' + (error.response?.data?.error || error.message))
      }
    }

    // 添加新标记组
    const handleAddMarkerGroup = () => {
      isEditingMarkerGroup.value = false
      markerGroupForm.value = {
        id: null,
        name: '',
        color: '#FF0000',
        is_visible: 1
      }
      markerGroupEditDialogVisible.value = true
    }

    // 编辑标记组
    const handleEditMarkerGroup = (group) => {
      isEditingMarkerGroup.value = true
      markerGroupForm.value = {
        id: group.id,
        name: group.name,
        color: group.color,
        is_visible: group.is_visible
      }
      markerGroupEditDialogVisible.value = true
    }

    // 保存标记组
    const saveMarkerGroup = async () => {
      try {
        loading.value = true
        
        const groupData = {
          name: markerGroupForm.value.name,
          color: markerGroupForm.value.color,
          is_visible: markerGroupForm.value.is_visible
        }
        
        let response
        if (isEditingMarkerGroup.value) {
          response = await axios.put(`http://localhost:5005/api/marker-groups/${markerGroupForm.value.id}`, groupData)
        } else {
          response = await axios.post('http://localhost:5005/api/marker-groups', groupData)
        }
        
        loading.value = false
        
        if (response.data.success) {
          ElMessage.success(isEditingMarkerGroup.value ? '标记组更新成功' : '标记组添加成功')
          markerGroupEditDialogVisible.value = false
          fetchMarkerGroups()
        } else {
          ElMessage.error(response.data.error || '保存标记组失败')
        }
      } catch (error) {
        loading.value = false
        console.error('Error saving marker group:', error)
        ElMessage.error('保存标记组失败: ' + (error.response?.data?.error || error.message))
      }
    }

    // 删除标记组
    const handleDeleteMarkerGroup = (group) => {
      ElMessageBox.confirm(
        '删除标记组将同时删除该组下的所有标记，确定要删除吗？',
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      ).then(async () => {
        try {
          loading.value = true
          const response = await axios.delete(`http://localhost:5005/api/marker-groups/${group.id}`)
          loading.value = false
          
          if (response.data.success) {
            ElMessage.success('标记组删除成功')
            fetchMarkerGroups()
            if (currentMarkerGroup.value && currentMarkerGroup.value.id === group.id) {
              showMarkersInGroup.value = false
              currentMarkerGroup.value = null
            }
          } else {
            ElMessage.error(response.data.error || '删除标记组失败')
          }
        } catch (error) {
          loading.value = false
          console.error('Error deleting marker group:', error)
          ElMessage.error('删除标记组失败: ' + (error.response?.data?.error || error.message))
        }
      }).catch(() => {
        // 用户取消操作
      })
    }

    // 切换标记组可见性
    const toggleMarkerGroupVisibility = async (groupId, isVisible) => {
      try {
        const response = await axios.put(`http://localhost:5005/api/marker-groups/${groupId}/toggle`, {
          is_visible: isVisible
        })
        
        if (response.data.success) {
          // 更新地图上的标记可见性
          updateMarkersVisibility(groupId, isVisible)
        } else {
          ElMessage.error(response.data.error || '更新可见性失败')
          // 回滚UI状态
          const group = markerGroups.value.find(g => g.id === groupId)
          if (group) {
            group.is_visible = !isVisible
          }
        }
      } catch (error) {
        console.error('Error toggling marker group visibility:', error)
        ElMessage.error('更新可见性失败: ' + (error.response?.data?.error || error.message))
        // 回滚UI状态
        const group = markerGroups.value.find(g => g.id === groupId)
        if (group) {
          group.is_visible = !isVisible
        }
      }
    }

    // 更新地图上标记的可见性
    const updateMarkersVisibility = (groupId, isVisible) => {
      // 获取该组的所有标记
      const groupMarkers = markers.value.filter(m => m.group_id === groupId)
      
      if (isVisible) {
        // 如果设置为可见，添加或显示该组的所有标记
        const group = markerGroups.value.find(g => g.id === groupId)
        if (group) {
          groupMarkers.forEach(marker => {
            if (markerLayers.value[marker.id]) {
              // 如果标记已存在，显示它
              markerLayers.value[marker.id].getElement().style.display = 'block'
            } else {
              // 如果标记不存在，添加它
              addMarkerToMap(marker, group)
            }
          })
        }
      } else {
        // 如果设置为不可见，隐藏该组的所有标记
        groupMarkers.forEach(marker => {
          if (markerLayers.value[marker.id]) {
            // 隐藏标记
            markerLayers.value[marker.id].getElement().style.display = 'none'
          }
        })
      }
    }

    // 定位到标记
    const locateToMarker = (marker) => {
      if (map && marker.latitude && marker.longitude) {
        map.flyTo({
          center: [marker.longitude, marker.latitude],
          zoom: 18,
          essential: true
        })
      }
    }

    // 删除标记
    const handleDeleteMarker = (marker) => {
      ElMessageBox.confirm(
        '确定要删除这个标记吗？',
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      ).then(async () => {
        try {
          loading.value = true
          const response = await axios.delete(`http://localhost:5005/api/markers/${marker.id}`)
          loading.value = false
          
          if (response.data.success) {
            ElMessage.success('标记删除成功')
            // 重新获取当前标记组的标记
            if (currentMarkerGroup.value) {
              handleViewMarkers(currentMarkerGroup.value.id)
            }
            // 从地图上移除标记
            removeMarkerFromMap(marker.id)
          } else {
            ElMessage.error(response.data.error || '删除标记失败')
          }
        } catch (error) {
          loading.value = false
          console.error('Error deleting marker:', error)
          ElMessage.error('删除标记失败: ' + (error.response?.data?.error || error.message))
        }
      }).catch(() => {
        // 用户取消操作
      })
    }

    // 从地图上移除标记
    const removeMarkerFromMap = (markerId) => {
      if (markerLayers.value[markerId]) {
        markerLayers.value[markerId].remove()
        delete markerLayers.value[markerId]
      }
    }

    // 添加标记
    const handleAddMarker = () => {
      // 首先检查是否有标记组
      if (markerGroups.value.length === 0) {
        // 如果没有标记组，提示先创建标记组
        ElMessageBox.confirm(
          '添加标记前需要先创建标记组，是否现在创建？',
          '提示',
          {
            confirmButtonText: '是',
            cancelButtonText: '否',
            type: 'info',
          }
        ).then(() => {
          // 打开标记组对话框
          showMarkerGroupDialog()
          handleAddMarkerGroup()
        }).catch(() => {
          // 用户取消操作
        })
        return
      }
      
      // 重置表单
      markerForm.value = {
        group_id: markerGroups.value.length > 0 ? markerGroups.value[0].id : null,
        marker_number: 1,
        latitude: null,
        longitude: null
      }
      markerLocationSelected.value = false
      addMarkerDialogVisible.value = true
    }

    // 开始选择标记位置
    const startSelectMarkerLocation = () => {
      isSelectingMarkerLocation.value = true
      addMarkerDialogVisible.value = false
      
      // 添加地图点击事件监听
      if (map) {
        map.once('click', handleMapClickForMarker)
        // 修改鼠标样式为十字光标
        map.getCanvas().style.cursor = 'crosshair'
      }
    }

    // 处理地图点击事件，记录标记位置
    const handleMapClickForMarker = (e) => {
      const { lng, lat } = e.lngLat
      
      // 恢复鼠标样式
      map.getCanvas().style.cursor = ''
      
      // 更新标记位置
      markerForm.value.latitude = lat
      markerForm.value.longitude = lng
      markerLocationSelected.value = true
      
      // 添加临时标记
      if (temporaryMarker.value) {
        temporaryMarker.value.remove()
      }
      
      // 创建一个新的临时标记
      const el = document.createElement('div')
      el.className = 'custom-marker'
      el.style.backgroundColor = 'rgba(255, 0, 0, 0.5)'
      el.style.borderRadius = '50%'
      el.style.width = '20px'
      el.style.height = '20px'
      el.style.border = '2px solid white'
      
      temporaryMarker.value = new mapboxgl.Marker({
        element: el,
        draggable: true
      })
        .setLngLat([lng, lat])
        .addTo(map)
      
      // 添加拖动事件监听
      temporaryMarker.value.on('dragend', () => {
        const newPosition = temporaryMarker.value.getLngLat()
        markerForm.value.latitude = newPosition.lat
        markerForm.value.longitude = newPosition.lng
      })
      
      // 重新打开对话框
      isSelectingMarkerLocation.value = false
      addMarkerDialogVisible.value = true
    }

    // 保存标记
    const saveMarker = async () => {
      try {
        loading.value = true
        
        const markerData = {
          group_id: markerForm.value.group_id,
          marker_number: markerForm.value.marker_number,
          latitude: markerForm.value.latitude,
          longitude: markerForm.value.longitude
        }
        
        const response = await axios.post('http://localhost:5005/api/markers', markerData)
        loading.value = false
        
        if (response.data.success) {
          ElMessage.success('标记添加成功')
          addMarkerDialogVisible.value = false
          
          // 移除临时标记
          if (temporaryMarker.value) {
            temporaryMarker.value.remove()
            temporaryMarker.value = null
          }
          
          // 刷新标记数据
          fetchAllMarkers()
          
          // 如果当前正在查看相关标记组，则刷新列表
          if (currentMarkerGroup.value && currentMarkerGroup.value.id === markerForm.value.group_id) {
            handleViewMarkers(currentMarkerGroup.value.id)
          }
        } else {
          ElMessage.error(response.data.error || '保存标记失败')
        }
      } catch (error) {
        loading.value = false
        console.error('Error saving marker:', error)
        ElMessage.error('保存标记失败: ' + (error.response?.data?.error || error.message))
      }
    }

    // 获取所有标记
    const fetchAllMarkers = async () => {
      try {
        const response = await axios.get('http://localhost:5005/api/markers')
        
        if (response.data.success) {
          markers.value = response.data.markers
          // 更新地图上的标记
          updateMarkersOnMap()
        }
      } catch (error) {
        console.error('Error fetching all markers:', error)
      }
    }

    // 在地图上更新所有标记
    const updateMarkersOnMap = () => {
      // 首先清除所有现有标记
      Object.values(markerLayers.value).forEach(marker => marker.remove())
      markerLayers.value = {}
      
      // 添加新的标记
      markers.value.forEach(marker => {
        const group = markerGroups.value.find(g => g.id === marker.group_id)
        // 只显示可见组的标记
        if (group && group.is_visible) {
          addMarkerToMap(marker, group)
        }
      })
    }

    // 在地图上添加标记
    const addMarkerToMap = (marker, group) => {
      if (!map) return
      
      // 创建标记DOM元素
      const el = document.createElement('div')
      el.className = 'custom-marker'
      el.style.backgroundColor = group.color
      el.style.borderRadius = '50%'
      el.style.width = '20px'
      el.style.height = '20px'
      el.style.border = '2px solid white'
      el.style.textAlign = 'center'
      el.style.lineHeight = '20px'
      el.style.color = 'white'
      el.style.fontWeight = 'bold'
      el.style.fontSize = '12px'
      el.innerText = marker.marker_number
      
      // 创建标记并添加到地图
      const mapMarker = new mapboxgl.Marker({
        element: el,
        draggable: true
      })
        .setLngLat([marker.longitude, marker.latitude])
        .addTo(map)
      
      // 存储标记对象用于后续操作
      markerLayers.value[marker.id] = mapMarker
      
      // 添加拖动事件，用于更新标记位置
      mapMarker.on('dragend', async () => {
        const newPosition = mapMarker.getLngLat()
        
        try {
          await axios.put(`http://localhost:5005/api/markers/${marker.id}`, {
            group_id: marker.group_id,
            marker_number: marker.marker_number,
            latitude: newPosition.lat,
            longitude: newPosition.lng
          })
          
          // 更新内存中的标记位置
          const markerIndex = markers.value.findIndex(m => m.id === marker.id)
          if (markerIndex !== -1) {
            markers.value[markerIndex].latitude = newPosition.lat
            markers.value[markerIndex].longitude = newPosition.lng
          }
          
          // 如果当前正在查看该标记组，更新列表
          if (currentMarkerGroup.value && currentMarkerGroup.value.id === marker.group_id) {
            const markerInGroupIndex = markersInGroup.value.findIndex(m => m.id === marker.id)
            if (markerInGroupIndex !== -1) {
              markersInGroup.value[markerInGroupIndex].latitude = newPosition.lat
              markersInGroup.value[markerInGroupIndex].longitude = newPosition.lng
            }
          }
        } catch (error) {
          console.error('Error updating marker position:', error)
          ElMessage.error('更新标记位置失败')
          // 回滚到原位置
          mapMarker.setLngLat([marker.longitude, marker.latitude])
        }
      })
      
      // 添加点击事件，定位到标记
      el.addEventListener('click', () => {
        locateToMarker(marker)
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
      showExportTypeDialog,
      showExportOffsetDialog,
      exportOffsetDialogVisible,
      handleExportOffsetDialogClose,
      applyExportOffset,
      confirmExportOffset,
      exportPoints,
      handleCheckAbnormalPoints,
      abnormalPoints,
      handleBoxSelect,
      isBoxSelecting,
      selectedPoints,
      offsetDialogVisible,
      offsetForm,
      handleOffsetPoints,
      handleOffsetDialogClose,
      vehicleSettings,
      isAddingVehicle,
      editVehicleDialogVisible,
      editVehicleForm,
      startAddVehicle,
      cancelAddVehicle,
      saveVehicle,
      handleEditVehicle,
      updateVehicle,
      handleDeleteVehicle,
      handleConfirmOffset,
      handleDeleteAbnormalPoints,
      currentLineWidth,
      wmsLayers,
      showWmsLayersMenu,
      wmsManagerDialogVisible,
      isAddingWmsLayer,
      editWmsLayerDialogVisible,
      editWmsLayerForm,
      handleOpenWmsLayerManager,
      startAddWmsLayer,
      cancelAddWmsLayer,
      saveWmsLayer,
      handleEditWmsLayer,
      updateWmsLayer,
      handleDeleteWmsLayer,
      toggleWmsLayer,
      offsetHistoryDialogVisible,
      offsetHistoryRecords,
      historyLoading,
      historyCurrentPage,
      historyPageSize,
      historyTotalCount,
      showOffsetHistoryDialog,
      fetchOffsetHistory,
      handleHistoryPageChange,
      formatTimestamp,
      obstacles,
      obstacleDialogVisible,
      obstacleListDialogVisible,
      obstacleForm,
      isDrawingObstacle,
      editingObstacle,
      handleObstacleDrawing,
      handleObstacleDialogClose,
      saveObstacle,
      showObstacleListDialog,
      locateObstacle,
      deleteObstacle,
      offsetPromptDialogVisible,
      uploadOffsetDialogVisible,
      uploaderOffsetData,
      handleOffsetPromptYes,
      handleOffsetPromptNo,
      handleUploadOffsetDialogClose,
      confirmUploadOffset,
      addOffsetRow,
      removeOffsetRow,
      applySpecificOffset,
      exportOffsetData,
      addExportOffsetRow,
      removeExportOffsetRow,
      isMeasuringDistance,
      measurePoints,
      measureLine,
      measureDistance,
      handleMeasureDistance,
      // Table management
      tableManagementDialogVisible,
      recordDialogVisible,
      isEditingRecord,
      tableRecords,
      currentPage,
      pageSize,
      totalRecords,
      recordForm,
      showTableManagementDialog,
      handleSizeChange,
      handleCurrentChange,
      handleAddTableRecord,
      handleEditTableRecord,
      saveTableRecord,
      handleDeleteTableRecord,
      exportToExcel,
      markerGroupDialogVisible,
      markerGroupEditDialogVisible,
      markerGroups,
      showMarkersInGroup,
      currentMarkerGroup,
      markersInGroup,
      isEditingMarkerGroup,
      markerGroupForm,
      addMarkerDialogVisible,
      isSelectingMarkerLocation,
      markerForm,
      markerLocationSelected,
      temporaryMarker,
      markers,
      markerLayers,
      showMarkerGroupDialog,
      fetchMarkerGroups,
      getMarkerCountByGroup,
      handleViewMarkers,
      handleAddMarkerGroup,
      handleEditMarkerGroup,
      saveMarkerGroup,
      handleDeleteMarkerGroup,
      toggleMarkerGroupVisibility,
      updateMarkersVisibility,
      locateToMarker,
      handleDeleteMarker,
      fetchAllMarkers,
      updateMarkersOnMap,
      addMarkerToMap,
      // 添加标记相关方法
      handleAddMarker,
      startSelectMarkerLocation,
      saveMarker,
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

/* 添加车辆表单样式 */
.add-vehicle-form {
  margin-top: 20px;
  padding: 15px;
  border-top: 1px solid #ebeef5;
}

.add-vehicle-btn {
  margin-top: 15px;
  text-align: center;
}

/* 颜色预览样式 */
.color-preview {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  display: inline-block;
  border: 1px solid #dcdfe6;
}

/* WMS图层菜单样式 */
.wms-layers-menu {
  position: absolute;
  top: 10px;
  right: 60px;
  width: 250px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  padding: 16px;
  z-index: 100;
}

.wms-layers-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.wms-layers-header h3 {
  margin: 0;
  font-size: 16px;
}

.wms-layers-list {
  max-height: 300px;
  overflow-y: auto;
}

.wms-layer-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.wms-layer-item:last-child {
  border-bottom: none;
}

.wms-layers-footer {
  text-align: center;
  padding-top: 10px;
}

/* WMS管理对话框样式 */
.wms-manager {
  margin-bottom: 20px;
}

.add-wms-layer {
  margin-top: 20px;
  padding: 15px;
  border-top: 1px solid #ebeef5;
}

.add-wms-layer-btn {
  margin-top: 15px;
  text-align: center;
}

.ellipsis-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

/* WMS图层切换按钮样式 */
.layer-toggle {
  padding: 5px 10px !important;
  background: white;
  border: none;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  color: #666;
}

.layer-toggle:hover {
  background: #f0f0f0;
}

/* 添加地图控制按钮样式 */
.map-controls {
  position: absolute;
  top: 70%;
  right: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 100;
  align-items: center;
  transform: translateY(-50%);
}

.control-button {
  width: 100px;
  height: 40px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  padding: 0 10px;
  text-align: center;
  margin: 0 auto;
}

.wms-button {
  background-color: #409EFF;
  border-color: #409EFF;
}

.wms-button:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

.zaw-button {
  background-color: #409EFF;
  border-color: #409EFF;
}

.zaw-button:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

.obstacles-list-button {
  background-color: #409EFF;
  border-color: #409EFF;
}

.obstacles-list-button:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

/* 添加颜色预览样式 */
.color-preview {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid #ddd;
  margin: 0 auto;
}

/* 障碍物表单样式 */
.obstacle-form {
  margin-top: 10px;
}

.color-picker-container {
  display: flex;
  align-items: center;
  gap: 15px;
}

.color-preview-large {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

/* 颜色预览行样式 */
.color-preview-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-value {
  font-size: 12px;
  color: #606266;
}

/* 添加航点偏移量设置对话框样式 */
.offset-prompt {
  text-align: center;
  font-size: 16px;
  margin: 20px 0;
}

.upload-offset-form {
  margin-bottom: 10px;
}

.upload-offset-desc {
  margin-bottom: 15px;
  font-size: 14px;
  color: #606266;
}

.upload-offset-form .add-btn {
  margin-top: 15px;
  text-align: center;
}

.upload-offset-form .confirm-btn {
  color: #67c23a;
}

.offset-preview {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.preview-title {
  font-weight: bold;
  margin-bottom: 10px;
}

.preview-content {
  position: relative;
  height: 120px;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 10px;
}

.preview-point {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.preview-point.original {
  background-color: #409EFF;
  left: 50px;
  top: 50px;
}

.preview-point.offset {
  background-color: #67c23a;
  border: 2px solid #fff;
  box-shadow: 0 0 4px rgba(0,0,0,0.3);
}

.preview-arrow {
  position: absolute;
  left: 65px;
  top: 46px;
  color: #909399;
}

.preview-info {
  text-align: center;
  font-size: 13px;
  color: #606266;
}

.measure-button {
  background-color: #E6A23C;
  border-color: #E6A23C;
}

.measure-button:hover {
  background-color: #ebb563;
  border-color: #ebb563;
}

/* Excel表格管理按钮样式 */
.excel-button {
  background-color: #67C23A;
  border-color: #67C23A;
}

.excel-button:hover {
  background-color: #85ce61;
  border-color: #85ce61;
}

/* 表格管理对话框样式 */
.table-management-container {
  padding: 10px;
}

.table-management-toolbar {
  margin-bottom: 15px;
  display: flex;
  justify-content: flex-start;
  gap: 10px;
}

.pagination-container {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

/* 添加颜色预览样式 */
.color-preview {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid #ddd;
  margin: 0 auto;
}

/* 障碍物表单样式 */
.obstacle-form {
  margin-top: 10px;
}

.color-picker-container {
  display: flex;
  align-items: center;
  gap: 15px;
}

.color-preview-large {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

/* 颜色预览行样式 */
.color-preview-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-value {
  font-size: 12px;
  color: #606266;
}

/* 添加航点偏移量设置对话框样式 */
.offset-prompt {
  text-align: center;
  font-size: 16px;
  margin: 20px 0;
}

.upload-offset-form {
  margin-bottom: 10px;
}

.upload-offset-desc {
  margin-bottom: 15px;
  font-size: 14px;
  color: #606266;
}

.upload-offset-form .add-btn {
  margin-top: 15px;
  text-align: center;
}

.upload-offset-form .confirm-btn {
  color: #67c23a;
}

.offset-preview {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.preview-title {
  font-weight: bold;
  margin-bottom: 10px;
}

.preview-content {
  position: relative;
  height: 120px;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 10px;
}

.preview-point {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.preview-point.original {
  background-color: #409EFF;
  left: 50px;
  top: 50px;
}

.preview-point.offset {
  background-color: #67c23a;
  border: 2px solid #fff;
  box-shadow: 0 0 4px rgba(0,0,0,0.3);
}

.preview-arrow {
  position: absolute;
  left: 65px;
  top: 46px;
  color: #909399;
}

.preview-info {
  text-align: center;
  font-size: 13px;
  color: #606266;
}

.measure-button {
  background-color: #E6A23C;
  border-color: #E6A23C;
}

.measure-button:hover {
  background-color: #ebb563;
  border-color: #ebb563;
}

/* 标记组按钮样式 */
.marker-group-button {
  background-color: #409EFF;
  border-color: #409EFF;
}

.marker-group-button:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

/* 添加标记按钮样式 */
.add-marker-button {
  background-color: #409EFF;
  border-color: #409EFF;
}

.add-marker-button:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

/* Excel表格管理按钮样式 */
.excel-button {
  background-color: #409EFF;
  border-color: #409EFF;
}

.excel-button:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

/* 标记组管理对话框样式 */
.marker-group-container {
  padding: 10px;
}

.marker-group-toolbar {
  margin-bottom: 15px;
  display: flex;
  justify-content: flex-start;
  gap: 10px;
}

.marker-list-container {
  margin-top: 20px;
  padding: 15px;
  border-top: 1px solid #ebeef5;
}

.marker-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.marker-list-header h3 {
  margin: 0;
  font-size: 16px;
}

.selected-location {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
}

.location-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 14px;
  color: #606266;
}

.custom-marker {
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
}

/* 表格管理对话框样式 */
.table-management-container {
  padding: 10px;
}
</style>