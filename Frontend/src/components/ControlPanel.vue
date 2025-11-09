<template>
  <div class="control-panel">
    <h2>🤖 ระบบควบคุมรดน้ำอัตโนมัติ</h2>

    <div class="main-controls">
      <button @click="captureAndDetect" :disabled="isLoading" class="btn-detect">
        📸 {{ isLoading ? 'กำลังประมวลผล (AI)...' : 'ถ่ายรูปและตรวจจับวัตถุ' }}
      </button>

      <button @click="LoadJsonFile" :disabled="isLoading" class="btn-loadjson">
        📁 {{ isLoading ? 'กำลังประมวลผล (JSON)...' : 'โหลดข้อมูลล่าสุด' }}
      </button>

      <button @click="waterAll" :disabled="isLoading || objectCount === 0" class="btn-water-all">
        💧 รดน้ำทั้งหมด ({{ objectCount }} จุด)
      </button>
    </div>

    <h3>🖼️ ภาพรวมผลลัพธ์ (Stitched + Detection)</h3>
    <div v-if="imageUrl" class="image-area">
      <img :src="imageUrl" alt="Stitched and Detected Image" class="result-image">
      <p class="status-message success">ตรวจพบวัตถุ {{ objectCount }} จุดพร้อมระบุตำแหน่ง!</p>
    </div>
    <p v-else-if="isLoading" class="status-message loading">กำลังรอภาพและผลลัพธ์จากเซิร์ฟเวอร์...</p>
    <p v-else class="status-message info">กรุณากดปุ่ม "ถ่ายรูปและตรวจจับวัตถุ" เพื่อเริ่มต้น</p>

    <div v-if="objectCount > 0" class="dynamic-controls">
      <h3>💦 รดน้ำเฉพาะจุด ({{ objectCount }} วัตถุที่ตรวจพบ)</h3>
      <div class="object-buttons">
        <button v-for="i in objectCount" :key="i" @click="waterSpecific(i)" :disabled="isLoading"
          :class="{ 'highlight': highlightedObject === i }" class="btn-specific">
          รดจุดที่ {{ i }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
// ... (โค้ดส่วน Script คงเดิม) ...
import axios from 'axios';

export default {
  name: 'ControlPanel',
  data() {
    return {
      backendBaseUrl: 'https://hydro-bot-7827.onrender.com',
      isLoading: false,
      imageUrl: '',
      objectCount: 0,
      highlightedObject: null
    };
  },
  methods: {
    async captureAndDetect() {
      this.isLoading = true;
      this.imageUrl = '';
      this.objectCount = 0;
      this.highlightedObject = null;

      try {
        const response = await axios.post(`${this.backendBaseUrl}/api/detect`, {}, { timeout: 180000 });
        const data = response.data;

        if (data.status === 'success' && data.image_url) {
          this.imageUrl = data.image_url;
          this.objectCount = data.object_count || 0;
          alert(`✅ ประมวลผลสำเร็จ! ตรวจพบวัตถุทั้งหมด ${this.objectCount} จุด`);
        } else {
          alert('❌ การตรวจจับล้มเหลว: ' + (data.message || 'โครงสร้างข้อมูลไม่ถูกต้อง'));
        }

      } catch (error) {
        console.error("API Error (Detect):", error);
        alert('❌ เกิดข้อผิดพลาดในการเชื่อมต่อ/ประมวลผล Render Backend');
      } finally {
        this.isLoading = false;
      }
    },
    async LoadJsonFile() {
      this.isLoading = true;
      this.imageUrl = ''

      try {
        const response = await axios.post(`${this.backendBaseUrl}/api/loadjson`);
        const data = response.data

        if (data.status === 'success' && data.image_url) {
          this.imageUrl = data.image_url;
          this.objectCount = data.objectCount || 0;
          alert(`✅ ประมวลผลสำเร็จ! ตรวจพบวัตถุทั้งหมด ${this.objectCount} จุด`);
        } else {
          alert('❌ การตรวจจับล้มเหลว: ' + (data.message || 'โครงสร้างข้อมูลไม่ถูกต้อง'));
        }
      }
      catch (error) {
        console.error("API Error (LoadingJson):", error);
        alert('❌ เกิดข้อผิดพลาดในการเชื่อมต่อ/ประมวลผล Render Backend');
      } finally {
        this.isLoading = false;
      }
    },

    async waterSpecific(objectId) {
      this.highlightedObject = objectId;
      try {
        const response = await axios.post(`${this.backendBaseUrl}/api/water`, { object_id: objectId });
        if (response.data.status === 'success') {
          alert(`💧 สั่งรดน้ำจุดที่ ${objectId} สำเร็จ! (คำสั่งถูกส่งไป Local Device แล้ว)`);
        } else {
          alert('❌ การสั่งรดน้ำเฉพาะจุดล้มเหลว');
        }
      } catch (error) {
        console.error("API Error (Specific Water):", error);
      }
    },

    async waterAll() {
      if (this.objectCount === 0) {
        alert("กรุณาตรวจจับวัตถุก่อน หรือไม่มีวัตถุให้รดน้ำ");
        return;
      }
      this.highlightedObject = null;
      try {
        const response = await axios.post(`${this.backendBaseUrl}/api/water_all`);
        if (response.data.status === 'success') {
          alert(`💧 สั่งรดน้ำทั้งหมด ${this.objectCount} จุด สำเร็จ! (คำสั่งถูกส่งไป Local Device แล้ว)`);
        } else {
          alert('❌ การสั่งรดน้ำทั้งหมดล้มเหลว');
        }
      } catch (error) {
        console.error("API Error (Water All):", error);
      }
    }
  }
};
</script>
<style scoped>
/* 🎨 Style ที่ปรับให้ Responsive */

/* Base Styles (ใช้ได้ดีบนทุกขนาดจอ) */
.control-panel {
  /* ปรับปรุง: เพิ่มความกว้างและ Padding */
  max-width: 1000px;
  /* ⬅️ NEW */
  width: 90%;
  margin: 30px auto;
  /* ⬅️ NEW */
  padding: 40px;
  /* ⬅️ NEW */
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  background-color: #f9f9f9;
}

h2 {
  font-size: 2rem;
  /* ⬅️ NEW */
  text-align: center;
  color: #333;
  margin-bottom: 30px;
  /* ⬅️ NEW */
}

h3 {
  font-size: 1.5rem;
  /* ⬅️ NEW */
  color: #42b983;
  margin-top: 30px;
  /* ⬅️ NEW */
}

/* Flex Container สำหรับปุ่ม - คงเดิม (Flexbox ดีอยู่แล้ว) */
.main-controls,
.object-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  /* ⬅️ เพิ่ม Gap ระหว่างปุ่มเล็กน้อย */
  justify-content: center;
}

/* Button Styles */
button {
  padding: 15px 30px;
  /* ⬅️ NEW */
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.3s, transform 0.1s;
  min-width: 180px;
  /* ⬅️ NEW */
  flex-grow: 1;
}

button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

button:disabled {
  background-color: #ccc !important;
  cursor: not-allowed;
  color: #666;
}

/* ---------------------------------------------------- */
/* 📱 MEDIA QUERIES (ปรับสำหรับหน้าจอขนาดเล็ก) - ส่วนนี้ยังคงเดิม เพื่อให้ Responsive ถูกต้อง */
/* ---------------------------------------------------- */
@media (max-width: 600px) {

  /* บนหน้าจอขนาดเล็ก (เช่น โทรศัพท์มือถือ) */
  .control-panel {
    margin: 10px auto;
    padding: 15px;
    width: 95%;
  }

  h2 {
    font-size: 1.3rem;
  }

  /* ทำให้ปุ่มหลักเรียงกันแบบเต็มความกว้าง */
  .main-controls button {
    min-width: 100%;
    margin-bottom: 5px;
    /* Padding ยังคงถูกปรับให้เล็กลงอัตโนมัติจากด้านบน */
  }

  /* ปุ่มรดน้ำเฉพาะจุด */
  .object-buttons {
    gap: 8px;
    justify-content: space-between;
  }

  .object-buttons button {
    flex-basis: calc(50% - 4px);
    min-width: unset;
    font-size: 0.9rem;
  }
}


/* Specific Button Colors และ Status Messages อื่นๆ คงเดิม */
.btn-detect {
  background-color: #007bff;
  color: white;
}

.btn-loadjson {
  background-color: #ff7300;
  color: white;
}

.btn-water-all {
  background-color: #42b983;
  color: white;
}

.btn-specific {
  background-color: #64b5f6;
  color: white;
}

.btn-specific.highlight {
  background-color: #ff9800;
  border: 3px solid #e65100;
  color: #333;
}

.image-area {
  text-align: center;
  margin: 25px 0;
}

.result-image {
  max-width: 100%;
  height: auto;
  border: 2px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.status-message {
  text-align: center;
  padding: 10px;
  border-radius: 4px;
  font-style: italic;
  margin-top: 15px;
}

.status-message.loading {
  background-color: #fff3cd;
  color: #856404;
}

.status-message.info {
  background-color: #e2e3e5;
  color: #666;
}

.status-message.success {
  background-color: #d4edda;
  color: #155724;
}
</style>