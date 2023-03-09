-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Mar 09, 2023 at 03:27 PM
-- Server version: 8.0.27
-- PHP Version: 7.4.26

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `groomer`
--

-- --------------------------------------------------------

--
-- Table structure for table `groomer`
--

DROP TABLE IF EXISTS `groomer`;
CREATE TABLE IF NOT EXISTS `groomer` (
  `groomerId` varchar(100) DEFAULT NULL,
  `groomerName` varchar(100) DEFAULT NULL,
  `groomerPicURL` varchar(100) DEFAULT NULL,
  `capacity` int DEFAULT NULL,
  `address` varchar(100) DEFAULT NULL,
  `contactNo` int DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `acceptablePetType` varchar(100) DEFAULT NULL,
  `membershipTier` varchar(100) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `groomer`
--

INSERT INTO `groomer` (`groomerId`, `groomerName`, `groomerPicURL`, `capacity`, `address`, `contactNo`, `email`, `acceptablePetType`, `membershipTier`) VALUES
('58723', 'Purrfect Grooming', 'https://uploads-ssl.webflow.com/6139cf517cd6d2b4af548b94/613a19d4ea090fe88fee09ca_pet-hotel-780x440.', 15, '123 Bukit Timah Road, Singapore', 67891234, 'info@purrfectgrooming.com.sg', 'cats', 'Premium'),
('23654', 'The Poodle Parlour', 'https://hips.hearstapps.com/edc.h-cdn.co/assets/17/02/2560x1899/best-dog-boarding-d-hotel.jpg?resize', 10, '10 Jalan Besar, Singapore', 98765432, 'info@poodleparlour.com.sg', 'dogs', 'General'),
('87521', 'Furry Friends Spa', 'https://uploads-ssl.webflow.com/606e96048e07f8de3d446a0b/62fca4d67b1adc75e74bf2ec_P9izERWKJMy3WtCFXc', 20, '45 East Coast Road, Singapore', 87654321, 'info@furryfriendsspa.com.sg', 'cats', 'General'),
('41236', 'Happy Tails Grooming', 'https://uploads-ssl.webflow.com/606e96048e07f8de3d446a0b/62fca4d6c0f79321c09de4d9_ElKiF-ZwAmb8Vc3FMu', 12, '1 Jurong West Avenue, Singapore', 65432109, 'info@happytailsgrooming.com.sg', 'dogs', 'General'),
('93217', 'Pawfection Grooming', 'https://uploads-ssl.webflow.com/606e96048e07f8de3d446a0b/62fb52ea65865b5c2b38e013_Mxhlj6pWRRDYS2twyi', 18, '77 Serangoon Road, Singapore', 89012345, 'info@pawfectiongrooming.com.sg', 'dogs', 'General'),
('48763', 'Pet Paradise', 'https://uploads-ssl.webflow.com/606e96048e07f8de3d446a0b/62fb52eb1e697bc47aeffa2d_wKk60FNfX2cVCXLc-7', 25, '36 Ang Mo Kio Avenue, Singapore', 76543210, 'info@petparadise.com.sg', 'cats', 'General'),
('23890', 'Pawsitive Grooming', 'https://uploads-ssl.webflow.com/606e96048e07f8de3d446a0b/62fca4d781de9f6164b09227_h_AiqYKT-vjlFm0pRl', 14, '55 Yishun Industrial Park, Singapore', 67890123, 'info@pawsitivegrooming.com.sg', 'dogs', 'General'),
('76549', 'Whiskers & Wags Grooming', 'https://jetpetresort.com/wp-content/uploads/2014/05/jet-palace.jpg', 10, '29 Lorong Mambong, Singapore', 90123456, 'info@whiskersandwagsgrooming.com.sg', 'cats', 'General'),
('23756', 'Doggy Doo', 'https://cdn.vox-cdn.com/thumbor/fnaPJnReyO6zNSOJMFHmKlwwovc=/0x0:3500x2336/1400x1400/filters:focal(1', 16, '10 Changi Village Road, Singapore', 78901234, 'info@doggydoo.com.sg', 'dogs', 'General'),
('34567', 'Furball Frenzy', 'https://www.naruwan-hotel.com.tw/en_new/NewImages/PitArea/img/PitArea%20(2).jpg', 20, '51 Hougang Avenue, Singapore', 65437890, 'info@furballfrenzy.com.sg', 'cats', 'General'),
('90876', 'The Barker Shop', 'https://scontent.fsin4-1.fna.fbcdn.net/v/t39.30808-6/306083044_174731381771471_1413778060914768815_n', 12, '63 Choa Chu Kang Road, Singapore', 78906543, 'info@barkershop.com.sg', 'dogs', 'General'),
('23456', 'Pampered Paws', 'https://shopee.sg/blog/wp-content/uploads/2022/06/How-to-choose-the-best-dog-boarding-service-in-Sin', 15, '8 Jalan Kayu, Singapore', 12345678, 'info@pamperedpaws.com.sg', 'dogs', 'General'),
('78901', 'Purrfect Pet Grooming', 'https://www.thebestsingapore.com/wp-content/uploads/2021/04/The-Waggington-2.jpg', 10, '18 Boon Lay Way, Singapore', 34567890, 'info@purrfectpetgrooming.com.sg', 'cats', 'General'),
('43567', 'Tails Up Grooming', 'https://siestacloudlivestorage.azureedge.net/default/medium_26654_95370a23-07aa-46ef-8dc8-6d7a2e4480', 18, '77 Upper East Coast Road, Singapore', 87654321, 'info@tailsupgrooming.com.sg', 'dogs', 'General'),
('76543', 'The Paw Spa', 'https://i.pinimg.com/originals/43/ad/40/43ad40572c70d44bf32aa501520c608e.jpg', 22, '6 Eu Tong Sen Street, Singapore', 23456789, 'info@pawspa.com.sg', 'cats', 'General'),
('35467', 'Doggy Delight', 'https://www.telegraph.co.uk/content/dam/family/2021/06/22/dog-hotel-love_4_trans_NvBQzQNjv4BqplGOf-d', 14, '2 Woodlands Avenue, Singapore', 78901234, 'info@doggydelight.com.sg', 'dogs', 'General'),
('98567', 'The Cat\'s Meow', 'https://cocomomo.my/images/rooms.jpg', 12, '9 Temasek Boulevard, Singapore', 34567890, 'info@thecatsmeow.com.sg', 'cats', 'General'),
('56789', 'Paws and Claws', 'https://img1.wsimg.com/isteam/ip/5484e2de-15b1-489e-95d5-2e80f0a7b41c/fb_5011265872258629_1822x2048-', 20, '27 Jalan Membina, Singapore', 98765432, 'info@pawsandclaws.com.sg', 'dogs', 'General'),
('45678', 'Furry Friends Grooming', 'https://s3-ap-southeast-1.amazonaws.com/atap-main/gallery-full/0bf2abbb-3cc6-4ee5-9cef-83b60037b333/', 15, '6 Raffles Boulevard, Singapore', 87654321, 'info@furryfriendsgrooming.com.sg', 'cats', 'General'),
('67890', 'Pawfect Grooming', 'https://npr.brightspotcdn.com/dims4/default/9213782/2147483647/strip/true/crop/1572x968+0+71/resize/', 12, '101 Upper Cross Street, Singapore', 23456789, 'info@pawfectgrooming.com.sg', 'dogs', 'General'),
('12345', 'Whiskers N Paws', 'https://static.thehoneycombers.com/wp-content/uploads/sites/2/2018/09/the-wagington.png', 18, '3 Simei Street 6, Singapore', 76543210, 'info@whiskersnpaws.com.sg', 'cats', 'General'),
('89012', 'Dapper Dogs', 'https://www.petplace.com/static/311e67c27b4d67333c454721869e8beb/c23ac/shutterstock_1065580706.jpg', 14, '2 Serangoon Road, Singapore', 34567890, 'info@dapperdogs.com.sg', 'dogs', 'General'),
('34567', 'Pawsitively Grooming', 'https://www.chinadaily.com.cn/business/img/attachement/jpg/site1/20160225/b083fe955aa11838d1e206.jpg', 20, '10 Tampines Central, Singapore', 65432109, 'info@pawsitivelygrooming.com.sg', 'cats', 'General'),
('90123', 'Furry Tails', 'https://cdn.shopify.com/s/files/1/0605/3888/0242/files/Pet_Hotel_480x480.jpg?v=1635352352', 10, '8 Marina Boulevard, Singapore', 12345678, 'info@furrytails.com.sg', 'dogs', 'General'),
('78901', 'Meow Grooming', 'https://media.bizj.us/view/img/12352627/k9-resorts-of-overland-park-luxury-suites-1*1200xx4032-2265-', 16, '50 Jurong Gateway Road, Singapore', 56789012, 'info@meowgrooming.com.sg', 'cats', 'General');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
